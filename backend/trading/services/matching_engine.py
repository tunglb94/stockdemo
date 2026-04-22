"""
Matching engine giả lập: khớp lệnh user với giá thị trường thực tế.
Logic: nếu giá thị trường thỏa điều kiện lệnh → khớp ngay, không cần tìm đối ứng.
"""
import logging
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from django.conf import settings
from market_data.models import PriceSnapshot
from trading.models import Order, Portfolio, Transaction, TPlusRecord
from accounts.models import Wallet

logger = logging.getLogger(__name__)


def try_match_order(order: Order) -> bool:
    """
    Thử khớp một lệnh với giá thị trường.
    Trả về True nếu lệnh được khớp (toàn phần hoặc một phần).
    """
    try:
        snapshot = order.stock.snapshots.latest("timestamp")
    except PriceSnapshot.DoesNotExist:
        logger.warning(f"Không có giá để khớp lệnh {order.id}")
        return False

    market_price = snapshot.current_price

    if order.side == "BUY":
        matched = _can_buy_match(order, market_price, snapshot)
    else:
        matched = _can_sell_match(order, market_price, snapshot)

    if matched:
        exec_price = _get_execution_price(order, market_price)
        _execute_order(order, exec_price, order.quantity)
        return True

    return False


def _can_buy_match(order: Order, market_price: Decimal, snapshot) -> bool:
    """Lệnh mua khớp khi giá thị trường <= giá đặt (hoặc lệnh MP/ATO/ATC)."""
    if order.order_type in ("MP", "ATO", "ATC"):
        return True
    return market_price <= order.price


def _can_sell_match(order: Order, market_price: Decimal, snapshot) -> bool:
    """Lệnh bán khớp khi giá thị trường >= giá đặt (hoặc lệnh MP/ATO/ATC)."""
    if order.order_type in ("MP", "ATO", "ATC"):
        return True
    return market_price >= order.price


def _get_execution_price(order: Order, market_price: Decimal) -> Decimal:
    """Xác định giá khớp thực tế."""
    if order.order_type in ("LO",) and order.price:
        # Lệnh LO khớp tại giá đặt nếu thị trường có lợi hơn, hoặc tại giá thị trường
        if order.side == "BUY":
            return min(order.price, market_price)
        else:
            return max(order.price, market_price)
    return market_price  # MP, ATO, ATC khớp tại giá thị trường


def _execute_order(order: Order, exec_price: Decimal, quantity: int):
    """Thực thi lệnh: cập nhật số dư, portfolio, tạo transaction."""
    with transaction.atomic():
        fee = exec_price * quantity * Decimal(str(settings.TRADING_FEE_RATE))
        tax = Decimal("0")

        if order.side == "BUY":
            _settle_buy(order, exec_price, quantity, fee)
        else:
            tax = exec_price * quantity * Decimal(str(settings.SELL_TAX_RATE))
            _settle_sell(order, exec_price, quantity, fee, tax)

        # Ghi transaction
        Transaction.objects.create(
            order=order,
            quantity=quantity,
            price=exec_price,
            amount=exec_price * quantity,
            fee=fee,
            tax=tax,
        )

        # Cập nhật trạng thái lệnh
        order.matched_quantity += quantity
        order.matched_price = exec_price
        order.status = "MATCHED" if order.matched_quantity >= order.quantity else "PARTIAL"
        order.save(update_fields=["matched_quantity", "matched_price", "status", "updated_at"])

        logger.info(
            f"Khớp lệnh: {order.side} {quantity} {order.stock.symbol} "
            f"@ {exec_price} | User: {order.user.email}"
        )


def _settle_buy(order: Order, exec_price: Decimal, quantity: int, fee: Decimal):
    """Sau khi lệnh mua khớp: trừ tiền, cộng cổ phiếu vào portfolio (T+2)."""
    wallet = Wallet.objects.select_for_update().get(user=order.user)
    total_cost = exec_price * quantity + fee

    # Hoàn phần dư frozen nếu giá khớp thấp hơn giá giam
    actual_freeze = exec_price * quantity * (1 + Decimal(str(settings.TRADING_FEE_RATE)))
    refund = order.frozen_amount - actual_freeze
    if refund > 0:
        wallet.unfreeze(refund)
        order.frozen_amount = actual_freeze
        order.save(update_fields=["frozen_amount"])

    wallet.deduct(total_cost)

    # Cập nhật portfolio (cổ phiếu nhận được nhưng chưa được bán ngay - T+2)
    portfolio, _ = Portfolio.objects.select_for_update().get_or_create(
        user=order.user,
        stock=order.stock,
        defaults={"avg_cost": exec_price},
    )

    # Tính giá vốn trung bình mới
    total_old = portfolio.quantity * portfolio.avg_cost
    total_new = quantity * exec_price
    new_total_qty = portfolio.quantity + quantity
    portfolio.avg_cost = (total_old + total_new) / new_total_qty if new_total_qty else exec_price
    portfolio.quantity = new_total_qty
    # Cổ phiếu mới mua chưa được vào available_quantity (T+2)
    portfolio.save(update_fields=["quantity", "avg_cost", "updated_at"])

    # Tạo record T+2
    today = date.today()
    t_plus_date = _next_trading_day(today, settings.T_PLUS_DAYS)
    TPlusRecord.objects.create(
        user=order.user,
        stock=order.stock,
        quantity=quantity,
        purchase_date=today,
        available_date=t_plus_date,
        order=order,
    )


def _settle_sell(order: Order, exec_price: Decimal, quantity: int, fee: Decimal, tax: Decimal):
    """Sau khi lệnh bán khớp: cộng tiền, trừ cổ phiếu khỏi portfolio."""
    wallet = Wallet.objects.select_for_update().get(user=order.user)
    proceeds = exec_price * quantity - fee - tax
    wallet.deposit(proceeds)

    portfolio = Portfolio.objects.select_for_update().get(user=order.user, stock=order.stock)
    portfolio.quantity -= quantity
    portfolio.frozen_quantity -= quantity
    if portfolio.quantity <= 0:
        portfolio.delete()
    else:
        portfolio.save(update_fields=["quantity", "frozen_quantity", "updated_at"])


def _next_trading_day(from_date: date, n_days: int) -> date:
    """Tính ngày giao dịch thứ n kể từ from_date (bỏ qua cuối tuần)."""
    result = from_date
    count = 0
    while count < n_days:
        result += timedelta(days=1)
        if result.weekday() < 5:  # 0-4 = thứ 2 đến thứ 6
            count += 1
    return result
