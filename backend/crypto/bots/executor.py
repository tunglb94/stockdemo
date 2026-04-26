import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


def execute_crypto_decisions(user, decisions: list, portfolio: dict, bot_reasoning: str = "") -> list:
    from crypto.models import CryptoAsset, CryptoWallet, CryptoPortfolio, CryptoOrder

    logs = []
    try:
        wallet = CryptoWallet.objects.get(user=user)
    except CryptoWallet.DoesNotExist:
        return ["  ERROR: CryptoWallet not found"]

    for d in decisions:
        action = str(d.get("action", "")).upper()
        symbol = str(d.get("symbol", "")).upper()
        reason = str(d.get("reason", ""))[:200]

        if action == "HOLD":
            logs.append(f"    HOLD: {reason}")
            continue

        if action not in ("BUY", "SELL") or not symbol:
            continue

        try:
            asset = CryptoAsset.objects.get(symbol=symbol, is_active=True)
            snap = asset.snapshots.latest("timestamp")
            price = snap.price_usd
        except Exception as e:
            logs.append(f"    SKIP {symbol}: {e}")
            continue

        if action == "BUY":
            try:
                quantity_usd = Decimal(str(d.get("quantity_usd", 0)))
            except (InvalidOperation, TypeError):
                continue

            if quantity_usd <= 0:
                continue

            wallet.refresh_from_db()
            if quantity_usd > wallet.balance_usd:
                quantity_usd = wallet.balance_usd * Decimal("0.95")

            if quantity_usd < Decimal("1"):
                logs.append(f"    SKIP BUY {symbol}: USD khong du")
                continue

            quantity = quantity_usd / price
            wallet.balance_usd -= quantity_usd
            wallet.save(update_fields=["balance_usd"])

            pos, _ = CryptoPortfolio.objects.get_or_create(
                user=user, asset=asset,
                defaults={"quantity": Decimal("0"), "avg_cost_usd": price},
            )
            new_qty = pos.quantity + quantity
            new_avg = (pos.avg_cost_usd * pos.quantity + price * quantity) / new_qty
            pos.quantity = new_qty
            pos.avg_cost_usd = new_avg
            pos.save()

            CryptoOrder.objects.create(
                user=user, asset=asset, side="BUY",
                quantity=quantity, price_usd=price, total_usd=quantity_usd,
                bot_reasoning=f"{bot_reasoning} | {reason}".strip(" |"),
            )
            logs.append(
                f"    BUY {symbol}: {float(quantity):.6f} @ ${float(price):.4f} (${float(quantity_usd):.2f}) | {reason}"
            )

        elif action == "SELL":
            try:
                quantity_pct = Decimal(str(d.get("quantity_pct", 100)))
            except (InvalidOperation, TypeError):
                quantity_pct = Decimal("100")

            quantity_pct = min(Decimal("100"), max(Decimal("1"), quantity_pct))

            try:
                pos = CryptoPortfolio.objects.get(user=user, asset=asset)
            except CryptoPortfolio.DoesNotExist:
                logs.append(f"    SKIP SELL {symbol}: khong co tai san")
                continue

            # Lưu cost_basis trước khi xóa/cập nhật portfolio
            cost_basis = pos.avg_cost_usd
            quantity = pos.quantity * quantity_pct / Decimal("100")
            total = quantity * price

            # Tính realized PnL
            cost_total = quantity * cost_basis
            pnl_usd = total - cost_total

            wallet.refresh_from_db()
            wallet.balance_usd += total
            wallet.save(update_fields=["balance_usd"])

            pos.quantity -= quantity
            if pos.quantity <= Decimal("0.00000001"):
                pos.delete()
            else:
                pos.save(update_fields=["quantity"])

            pnl_pct = float((price - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0

            CryptoOrder.objects.create(
                user=user, asset=asset, side="SELL",
                quantity=quantity, price_usd=price, total_usd=total,
                bot_reasoning=f"{bot_reasoning} | {reason}".strip(" |"),
                cost_basis_usd=cost_basis,
                pnl_usd=pnl_usd,
            )

            pnl_label = "hoa" if abs(pnl_pct) < 0.01 else f"{pnl_pct:+.2f}%"
            logs.append(
                f"    SELL {symbol}: {float(quantity):.6f} @ ${float(price):.4f} "
                f"(${float(total):.2f}) PnL={pnl_label} | {reason}"
            )

    return logs
