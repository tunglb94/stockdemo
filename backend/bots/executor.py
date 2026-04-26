"""
Thực thi lệnh trading cho bot dựa trên quyết định từ LLM.
"""
import logging
from decimal import Decimal
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def execute_decisions(user, decisions: list, portfolio: dict) -> list[str]:
    """
    Thực thi danh sách quyết định từ LLM.
    Trả về log các lệnh đã đặt.
    """
    from trading.models import Order
    from market_data.models import Stock, PriceSnapshot
    from accounts.models import Wallet
    from trading.services.matching_engine import try_match_order

    logs = []
    wallet = Wallet.objects.get(user=user)

    for dec in decisions:
        # Refresh wallet từ DB trước mỗi lệnh — tránh dùng balance stale
        wallet.refresh_from_db()

        symbol = dec.get("symbol", "").upper()
        action = dec.get("action", "").upper()
        quantity = int(dec.get("quantity", 0))
        reason = dec.get("reason", "")

        if action not in ("BUY", "SELL") or quantity <= 0:
            continue
        if quantity % 100 != 0:
            quantity = (quantity // 100) * 100
        if quantity == 0:
            continue

        try:
            stock = Stock.objects.get(symbol=symbol, is_active=True)
            snap = stock.snapshots.latest("timestamp")
            market_price = snap.current_price
        except Exception:
            logs.append(f"  ❌ {symbol}: không có dữ liệu giá")
            continue

        if action == "BUY":
            cost = market_price * quantity * Decimal("1.0015")
            if cost > wallet.available_balance:  # Dùng available (balance - frozen)
                # Giảm số lượng cho vừa túi tiền
                max_qty = int(wallet.available_balance / (market_price * Decimal("1.0015")) // 100) * 100
                if max_qty < 100:
                    logs.append(f"  ❌ {symbol}: không đủ tiền mua {quantity} cổ")
                    continue
                quantity = max_qty

            order = Order.objects.create(
                user=user,
                stock=stock,
                side="BUY",
                order_type="MP",  # Market price — khớp ngay
                price=market_price,
                quantity=quantity,
                status="PENDING",
                frozen_amount=market_price * quantity * Decimal("1.0015"),
            )
            wallet.freeze(order.frozen_amount)
            if try_match_order(order):
                logs.append(f"  ✅ MUA {quantity} {symbol} @ {market_price/1000:.2f} | {reason}")
            else:
                logs.append(f"  ⏳ MUA {quantity} {symbol} đặt chờ @ {market_price/1000:.2f}")

        elif action == "SELL":
            pos = portfolio.get(symbol)
            if not pos:
                logs.append(f"  ❌ {symbol}: không có trong danh mục")
                continue
            avail = pos["available_quantity"]
            if avail <= 0:
                logs.append(f"  ❌ {symbol}: chưa qua T+2, chưa bán được")
                continue
            quantity = min(quantity, avail)

            order = Order.objects.create(
                user=user,
                stock=stock,
                side="SELL",
                order_type="MP",
                price=market_price,
                quantity=quantity,
                status="PENDING",
                frozen_amount=Decimal("0"),
            )
            # Freeze cổ phiếu
            from trading.models import Portfolio as PortfolioModel
            port = PortfolioModel.objects.get(user=user, stock=stock)
            port.frozen_quantity += quantity
            port.save(update_fields=["frozen_quantity"])

            if try_match_order(order):
                logs.append(f"  ✅ BÁN {quantity} {symbol} @ {market_price/1000:.2f} | {reason}")
            else:
                logs.append(f"  ⏳ BÁN {quantity} {symbol} đặt chờ @ {market_price/1000:.2f}")

    return logs
