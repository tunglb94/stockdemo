"""
Validate và đặt lệnh. Giam tiền/cổ phiếu trước khi lệnh được khớp.
"""
import logging
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from market_data.models import Stock, PriceSnapshot
from accounts.models import Wallet
from trading.models import Order, Portfolio

logger = logging.getLogger(__name__)


def validate_and_place_order(user, data: dict) -> Order:
    """
    Validate lệnh mua/bán và giam vốn tương ứng.
    Raise ValueError nếu có lỗi nghiệp vụ.
    """
    symbol = data["symbol"].upper()
    side = data["side"]
    order_type = data["order_type"]
    quantity = int(data["quantity"])
    price = Decimal(str(data.get("price", 0))) if data.get("price") else None

    if quantity <= 0 or quantity % 100 != 0:
        raise ValueError("Khối lượng phải là bội số của 100 (1 lô = 100 cổ phiếu).")

    stock = Stock.objects.get(symbol=symbol, is_active=True)

    # Lấy snapshot giá hiện tại để validate giá trần/sàn
    try:
        snapshot = stock.snapshots.latest("timestamp")
    except PriceSnapshot.DoesNotExist:
        raise ValueError(f"Chưa có dữ liệu giá cho {symbol}. Vui lòng thử lại.")

    # Validate giá lệnh LO trong khoảng trần/sàn
    if order_type == "LO" and price:
        if price > snapshot.ceiling_price:
            raise ValueError(f"Giá đặt ({price}) vượt giá trần ({snapshot.ceiling_price}).")
        if price < snapshot.floor_price:
            raise ValueError(f"Giá đặt ({price}) thấp hơn giá sàn ({snapshot.floor_price}).")

    with transaction.atomic():
        if side == "BUY":
            order = _place_buy_order(user, stock, order_type, quantity, price, snapshot)
        else:
            order = _place_sell_order(user, stock, order_type, quantity, price, snapshot)

    return order


def _place_buy_order(user, stock, order_type, quantity, price, snapshot) -> Order:
    """Giam tiền và tạo lệnh mua."""
    wallet = Wallet.objects.select_for_update().get(user=user)

    # Dùng giá trần để giam tiền tối đa (an toàn nhất cho lệnh MP)
    freeze_price = price if price else snapshot.ceiling_price
    required_amount = freeze_price * quantity
    # Cộng thêm phí dự phòng
    fee_reserve = required_amount * Decimal(str(settings.TRADING_FEE_RATE))
    total_freeze = required_amount + fee_reserve

    if wallet.available_balance < total_freeze:
        raise ValueError(
            f"Số dư khả dụng ({wallet.available_balance:,.0f} VNĐ) "
            f"không đủ để đặt lệnh ({total_freeze:,.0f} VNĐ)."
        )

    wallet.freeze(total_freeze)

    order = Order.objects.create(
        user=user,
        stock=stock,
        order_type=order_type,
        side="BUY",
        quantity=quantity,
        price=price,
        frozen_amount=total_freeze,
        status="PENDING",
    )
    logger.info(f"Lệnh MUA tạo: {user.email} | {stock.symbol} x{quantity} @ {price}")
    return order


def _place_sell_order(user, stock, order_type, quantity, price, snapshot) -> Order:
    """Giam cổ phiếu và tạo lệnh bán."""
    portfolio = Portfolio.objects.select_for_update().filter(user=user, stock=stock).first()

    if not portfolio or portfolio.available_quantity < quantity:
        available = portfolio.available_quantity if portfolio else 0
        raise ValueError(
            f"Số cổ phiếu {stock.symbol} có thể bán ({available}) không đủ "
            f"(yêu cầu {quantity}). Lưu ý: cổ phiếu mua hôm nay phải chờ T+2."
        )

    # Giam cổ phiếu
    portfolio.available_quantity -= quantity
    portfolio.frozen_quantity += quantity
    portfolio.save(update_fields=["available_quantity", "frozen_quantity", "updated_at"])

    order = Order.objects.create(
        user=user,
        stock=stock,
        order_type=order_type,
        side="SELL",
        quantity=quantity,
        price=price,
        frozen_amount=Decimal("0"),
        status="PENDING",
    )
    logger.info(f"Lệnh BÁN tạo: {user.email} | {stock.symbol} x{quantity} @ {price}")
    return order


def cancel_order(user, order: Order):
    """Hủy lệnh chờ và hoàn trả tiền/cổ phiếu đã giam."""
    if order.user != user:
        raise ValueError("Bạn không có quyền hủy lệnh này.")
    if order.status not in ("PENDING", "PARTIAL"):
        raise ValueError(f"Không thể hủy lệnh đang ở trạng thái '{order.status}'.")

    with transaction.atomic():
        if order.side == "BUY":
            wallet = Wallet.objects.select_for_update().get(user=user)
            wallet.unfreeze(order.frozen_amount)
        else:
            portfolio = Portfolio.objects.select_for_update().get(user=user, stock=order.stock)
            portfolio.available_quantity += order.remaining_quantity
            portfolio.frozen_quantity -= order.remaining_quantity
            portfolio.save(update_fields=["available_quantity", "frozen_quantity", "updated_at"])

        order.status = "CANCELLED"
        order.save(update_fields=["status", "updated_at"])

    logger.info(f"Hủy lệnh: {order.id} | {user.email}")
