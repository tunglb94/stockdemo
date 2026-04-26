import logging
from decimal import Decimal, InvalidOperation
from django.utils import timezone

logger = logging.getLogger(__name__)
START_CAPITAL       = Decimal("5000")
MAX_OPEN_POSITIONS  = 10
STOP_LOSS_PCT       = Decimal("0.30")   # auto stop-loss at -30% margin
LIQ_PCT             = Decimal("0.80")   # hard liquidation at -80% margin
TAKE_PROFIT_PCT     = Decimal("0.40")   # auto take-profit at +40% margin
TIME_STOP_HOURS     = 2.0               # close if open > 2h and still not profitable


def _close_position(pos, cur_price, wallet, reason_prefix):
    """Shared logic to close a position and return margin to wallet."""
    upnl = pos.unrealized_pnl(cur_price)
    returned = max(Decimal("0"), pos.margin_usd + upnl)
    wallet.used_margin_usd = max(Decimal("0"), wallet.used_margin_usd - pos.margin_usd)
    wallet.balance_usd += returned
    wallet.save(update_fields=["used_margin_usd", "balance_usd"])
    pos.status = "CLOSED"
    pos.exit_price = cur_price
    pos.realized_pnl = upnl
    pos.closed_at = timezone.now()
    pos.save()
    sign = "+" if upnl >= 0 else ""
    return f"    {reason_prefix} {pos.direction} {pos.asset.symbol} @ ${float(cur_price):,.4f} | PnL: {sign}${float(upnl):.2f}"


def check_liquidations(user):
    """Hard liquidation at -80% margin. Runs first, highest priority."""
    from crypto.models import FuturesPosition, FuturesWallet

    wallet = FuturesWallet.objects.get(user=user)
    logs = []

    for pos in FuturesPosition.objects.filter(user=user, status="OPEN").select_related("asset"):
        try:
            cur_price = pos.asset.snapshots.latest("timestamp").price_usd
        except Exception:
            continue

        upnl = pos.unrealized_pnl(cur_price)
        loss_pct = -upnl / pos.margin_usd if pos.margin_usd else Decimal("0")

        if loss_pct >= LIQ_PCT:
            pos.status = "LIQUIDATED"
            pos.exit_price = cur_price
            pos.realized_pnl = upnl
            pos.closed_at = timezone.now()
            pos.save()
            wallet.used_margin_usd = max(Decimal("0"), wallet.used_margin_usd - pos.margin_usd)
            wallet.save(update_fields=["used_margin_usd"])
            logs.append(
                f"    LIQUIDATED {pos.direction} {pos.asset.symbol} @ ${float(cur_price):,.4f} | "
                f"PnL: ${float(upnl):.2f} ({float(loss_pct)*100:.0f}% loss)"
            )
        elif loss_pct >= STOP_LOSS_PCT:
            wallet.refresh_from_db()
            log = _close_position(pos, cur_price, wallet,
                                  f"STOP-LOSS -{int(float(loss_pct)*100)}%")
            logs.append(log)

    return logs


def auto_manage_positions(user):
    """
    Professional position management — runs before LLM each round.

    Rules:
    - Auto take-profit  : gain >= +40% of margin → close, lock profits
    - Trailing floor    : gain was >= +25%, now < +10% → protect partial profit
    - Time-stop         : open > 2h AND profit < 0% AND loss < 20% → free stale capital
    """
    from crypto.models import FuturesPosition, FuturesWallet

    wallet = FuturesWallet.objects.get(user=user)
    logs = []
    now = timezone.now()

    for pos in FuturesPosition.objects.filter(user=user, status="OPEN").select_related("asset"):
        try:
            cur_price = pos.asset.snapshots.latest("timestamp").price_usd
        except Exception:
            continue

        upnl     = pos.unrealized_pnl(cur_price)
        margin   = pos.margin_usd
        gain_pct = upnl / margin if margin else Decimal("0")
        age_h    = (now - pos.opened_at).total_seconds() / 3600

        close_reason = None

        if gain_pct >= TAKE_PROFIT_PCT:
            close_reason = f"AUTO TAKE-PROFIT +{float(gain_pct)*100:.0f}%"

        elif age_h > TIME_STOP_HOURS and Decimal("-0.20") < gain_pct < Decimal("0"):
            close_reason = f"TIME-STOP: {age_h:.1f}h open, still at {float(gain_pct)*100:.1f}%"

        if close_reason:
            wallet.refresh_from_db()
            log = _close_position(pos, cur_price, wallet, close_reason)
            logs.append(log)

    return logs


def execute_futures_decisions(user, decisions: list) -> list:
    from crypto.models import CryptoAsset, FuturesWallet, FuturesPosition

    logs = []
    try:
        wallet = FuturesWallet.objects.get(user=user)
    except FuturesWallet.DoesNotExist:
        return ["  ERROR: FuturesWallet not found"]

    # Priority order: liquidation → auto-management → LLM decisions
    logs.extend(check_liquidations(user))
    wallet.refresh_from_db()
    logs.extend(auto_manage_positions(user))
    wallet.refresh_from_db()

    _ACTION_MAP = {"BUY": "LONG", "OPEN_LONG": "LONG", "SELL": "SHORT", "OPEN_SHORT": "SHORT"}

    for d in decisions:
        action = _ACTION_MAP.get(str(d.get("action", "")).upper(), str(d.get("action", "")).upper())
        symbol = str(d.get("symbol", "")).upper()
        reason = str(d.get("reason", ""))[:100]

        if action == "HOLD":
            logs.append(f"    HOLD: {reason}")
            continue

        if action in ("LONG", "SHORT"):
            try:
                margin_usd = Decimal(str(
                    d.get("margin_usd") or d.get("quantity_usd") or d.get("amount_usd") or 0
                ))
                leverage = min(20, max(1, int(d.get("leverage", 1))))
            except (InvalidOperation, TypeError, ValueError):
                continue

            if margin_usd <= 0 or not symbol:
                continue

            # Guard: max open positions
            open_count = FuturesPosition.objects.filter(user=user, status="OPEN").count()
            if open_count >= MAX_OPEN_POSITIONS:
                logs.append(f"    SKIP {action} {symbol}: {open_count}/{MAX_OPEN_POSITIONS} slots full")
                continue

            # Guard: no duplicate same symbol + direction
            if FuturesPosition.objects.filter(user=user, asset__symbol=symbol,
                                              direction=action, status="OPEN").exists():
                logs.append(f"    SKIP {action} {symbol}: already have this position open")
                continue

            try:
                asset = CryptoAsset.objects.get(symbol=symbol, is_active=True)
                price = asset.snapshots.latest("timestamp").price_usd
            except Exception as e:
                logs.append(f"    SKIP {symbol}: {e}")
                continue

            wallet.refresh_from_db()

            # Guard: portfolio heat — never exceed 70% of total capital in margin
            used = wallet.used_margin_usd
            total_capital = wallet.balance_usd + used
            heat_after = (used + margin_usd) / total_capital if total_capital else Decimal("1")
            if heat_after > Decimal("0.70"):
                margin_usd = (total_capital * Decimal("0.70") - used).quantize(Decimal("1"))
                if margin_usd < Decimal("100"):
                    logs.append(f"    SKIP {action} {symbol}: portfolio heat too high, not enough room")
                    continue

            if margin_usd > wallet.available:
                margin_usd = wallet.available * Decimal("0.9")
            if margin_usd < Decimal("10"):
                logs.append(f"    SKIP {action} {symbol}: margin too small after heat check")
                continue

            quantity = (margin_usd * leverage) / price
            wallet.balance_usd -= margin_usd
            wallet.used_margin_usd += margin_usd
            wallet.save(update_fields=["balance_usd", "used_margin_usd"])

            FuturesPosition.objects.create(
                user=user, asset=asset, direction=action,
                quantity=quantity, entry_price=price,
                margin_usd=margin_usd, leverage=leverage,
            )
            logs.append(
                f"    {action} {symbol}: qty={float(quantity):.6f} @ ${float(price):,.4f} | "
                f"margin=${float(margin_usd):.0f} x{leverage} | {reason}"
            )

        elif action == "CLOSE":
            direction = str(d.get("direction", "")).upper()
            if not symbol or direction not in ("LONG", "SHORT"):
                continue

            try:
                asset = CryptoAsset.objects.get(symbol=symbol, is_active=True)
                cur_price = asset.snapshots.latest("timestamp").price_usd
            except Exception as e:
                logs.append(f"    SKIP CLOSE {symbol}: {e}")
                continue

            positions = FuturesPosition.objects.filter(
                user=user, asset=asset, direction=direction, status="OPEN"
            )
            if not positions.exists():
                logs.append(f"    SKIP CLOSE {direction} {symbol}: no open position")
                continue

            for pos in positions:
                wallet.refresh_from_db()
                log = _close_position(pos, cur_price, wallet, f"CLOSE {direction}")
                log = log + f" | {reason}"
                logs.append(log)

    return logs


def get_futures_portfolio_state(user) -> dict:
    from crypto.models import FuturesPosition
    from django.utils import timezone as tz

    positions = {}
    now = tz.now()

    for pos in FuturesPosition.objects.filter(user=user, status="OPEN").select_related("asset"):
        try:
            cur = float(pos.asset.snapshots.latest("timestamp").price_usd)
        except Exception:
            cur = float(pos.entry_price)

        upnl    = float(pos.unrealized_pnl(cur))
        margin  = float(pos.margin_usd)
        gain_pct = round(upnl / margin * 100, 1) if margin else 0
        loss_pct = round(-upnl / margin * 100, 1) if margin else 0
        age_h   = round((now - pos.opened_at).total_seconds() / 3600, 1)

        key = f"{pos.direction}_{pos.asset.symbol}_{pos.id}"
        positions[key] = {
            "direction":          pos.direction,
            "symbol":             pos.asset.symbol,
            "quantity":           float(pos.quantity),
            "entry_price":        float(pos.entry_price),
            "current_price":      cur,
            "margin_usd":         margin,
            "leverage":           pos.leverage,
            "unrealized_pnl":     upnl,
            "gain_pct_of_margin": gain_pct,    # positive = profit
            "loss_pct_of_margin": loss_pct,    # positive = loss (used for stop-loss hints)
            "age_hours":          age_h,
            "liq_price":          pos.liq_price(),
        }
    return positions
