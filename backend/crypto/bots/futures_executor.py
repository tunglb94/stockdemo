import logging
from decimal import Decimal, InvalidOperation
from django.utils import timezone

logger = logging.getLogger(__name__)
START_CAPITAL = Decimal("5000")


def check_liquidations(user):
    """Thanh ly cac vi tri lo > 80% margin."""
    from crypto.models import FuturesPosition, FuturesWallet

    wallet = FuturesWallet.objects.get(user=user)
    liquidated = []

    for pos in FuturesPosition.objects.filter(user=user, status="OPEN").select_related("asset"):
        try:
            snap = pos.asset.snapshots.latest("timestamp")
            cur_price = snap.price_usd
        except Exception:
            continue

        upnl = pos.unrealized_pnl(cur_price)
        if upnl < -pos.margin_usd * Decimal("0.8"):
            # Liquidate
            pos.status = "LIQUIDATED"
            pos.exit_price = cur_price
            pos.realized_pnl = upnl
            pos.closed_at = timezone.now()
            pos.save()

            # Margin was already deducted from balance when opening — just unlock used_margin
            wallet.used_margin_usd = max(Decimal("0"), wallet.used_margin_usd - pos.margin_usd)
            wallet.save(update_fields=["used_margin_usd"])
            liquidated.append(f"LIQUIDATED {pos.direction} {pos.asset.symbol} @ ${float(cur_price):.2f} | PnL: ${float(upnl):.2f}")

    return liquidated


def execute_futures_decisions(user, decisions: list) -> list:
    from crypto.models import CryptoAsset, FuturesWallet, FuturesPosition

    logs = []
    try:
        wallet = FuturesWallet.objects.get(user=user)
    except FuturesWallet.DoesNotExist:
        return ["  ERROR: FuturesWallet not found"]

    # Check liquidations first
    liq_logs = check_liquidations(user)
    logs.extend(liq_logs)
    wallet.refresh_from_db()

    # Normalize action aliases (some models use BUY/SELL instead of LONG/SHORT)
    _ACTION_MAP = {"BUY": "LONG", "OPEN_LONG": "LONG", "SELL": "SHORT", "OPEN_SHORT": "SHORT"}

    for d in decisions:
        action = str(d.get("action", "")).upper()
        action = _ACTION_MAP.get(action, action)
        symbol = str(d.get("symbol", "")).upper()
        reason = str(d.get("reason", ""))[:80]

        if action == "HOLD":
            logs.append(f"    HOLD: {reason}")
            continue

        if action in ("LONG", "SHORT"):
            try:
                # Support margin_usd, quantity_usd, amount_usd as aliases
                margin_usd = Decimal(str(
                    d.get("margin_usd") or d.get("quantity_usd") or d.get("amount_usd") or 0
                ))
                leverage = min(20, max(1, int(d.get("leverage", 1))))
            except (InvalidOperation, TypeError, ValueError):
                continue

            if margin_usd <= 0 or not symbol:
                continue

            try:
                asset = CryptoAsset.objects.get(symbol=symbol, is_active=True)
                snap = asset.snapshots.latest("timestamp")
                price = snap.price_usd
            except Exception as e:
                logs.append(f"    SKIP {symbol}: {e}")
                continue

            wallet.refresh_from_db()
            if margin_usd > wallet.available:
                margin_usd = wallet.available * Decimal("0.9")

            if margin_usd < Decimal("10"):
                logs.append(f"    SKIP {action} {symbol}: margin qua nho")
                continue

            notional = margin_usd * leverage
            quantity = notional / price

            # Deduct margin from balance when opening (returned on close/liquidation)
            wallet.balance_usd -= margin_usd
            wallet.used_margin_usd += margin_usd
            wallet.save(update_fields=["balance_usd", "used_margin_usd"])

            FuturesPosition.objects.create(
                user=user, asset=asset, direction=action,
                quantity=quantity, entry_price=price,
                margin_usd=margin_usd, leverage=leverage,
            )
            logs.append(
                f"    {action} {symbol}: {float(quantity):.6f} @ ${float(price):,.2f} | margin=${float(margin_usd):.0f} x{leverage} | {reason}"
            )

        elif action == "CLOSE":
            direction = str(d.get("direction", "")).upper()
            if not symbol or direction not in ("LONG", "SHORT"):
                continue

            try:
                asset = CryptoAsset.objects.get(symbol=symbol, is_active=True)
                snap = asset.snapshots.latest("timestamp")
                cur_price = snap.price_usd
            except Exception as e:
                logs.append(f"    SKIP CLOSE {symbol}: {e}")
                continue

            positions = FuturesPosition.objects.filter(
                user=user, asset=asset, direction=direction, status="OPEN"
            )
            if not positions.exists():
                logs.append(f"    SKIP CLOSE {direction} {symbol}: khong co vi tri")
                continue

            for pos in positions:
                upnl = pos.unrealized_pnl(cur_price)
                returned = pos.margin_usd + upnl

                wallet.refresh_from_db()
                wallet.used_margin_usd = max(Decimal("0"), wallet.used_margin_usd - pos.margin_usd)
                wallet.balance_usd += max(Decimal("0"), returned)
                wallet.save(update_fields=["used_margin_usd", "balance_usd"])

                pos.status = "CLOSED"
                pos.exit_price = cur_price
                pos.realized_pnl = upnl
                pos.closed_at = timezone.now()
                pos.save()

                sign = "+" if upnl >= 0 else ""
                logs.append(
                    f"    CLOSE {direction} {symbol} @ ${float(cur_price):,.2f} | PnL: {sign}${float(upnl):.2f} | {reason}"
                )

    return logs


def get_futures_portfolio_state(user) -> dict:
    from crypto.models import FuturesPosition

    positions = {}
    for pos in FuturesPosition.objects.filter(user=user, status="OPEN").select_related("asset"):
        try:
            snap = pos.asset.snapshots.latest("timestamp")
            cur = float(snap.price_usd)
        except Exception:
            cur = float(pos.entry_price)

        upnl = float(pos.unrealized_pnl(cur))
        key = f"{pos.direction}_{pos.asset.symbol}_{pos.id}"
        positions[key] = {
            "direction": pos.direction,
            "symbol": pos.asset.symbol,
            "quantity": float(pos.quantity),
            "entry_price": float(pos.entry_price),
            "current_price": cur,
            "margin_usd": float(pos.margin_usd),
            "leverage": pos.leverage,
            "unrealized_pnl": upnl,
            "liq_price": pos.liq_price(),
        }
    return positions
