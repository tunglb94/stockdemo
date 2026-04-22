"""
Xử lý và lưu dữ liệu giá vào database sau khi fetch từ vnstock.
"""
import logging
from decimal import Decimal
from .vnstock_client import VN30_SYMBOLS, VN30_COMPANY_NAMES

logger = logging.getLogger(__name__)


def ensure_vn30_stocks_exist():
    """Đảm bảo tất cả mã VN30 đã có trong DB. Dùng tên công ty hardcode."""
    from market_data.models import Stock

    for symbol in VN30_SYMBOLS:
        Stock.objects.get_or_create(
            symbol=symbol,
            defaults={
                "company_name": VN30_COMPANY_NAMES.get(symbol, symbol),
                "exchange": "HOSE",
                "is_vn30": True,
                "is_active": True,
            },
        )
    logger.info(f"Đã đảm bảo {len(VN30_SYMBOLS)} mã VN30 trong DB.")


def save_price_snapshot(price_data: dict) -> bool:
    """Lưu một snapshot giá vào DB và broadcast qua WebSocket."""
    from market_data.models import Stock, PriceSnapshot

    try:
        stock = Stock.objects.get(symbol=price_data["symbol"])
    except Stock.DoesNotExist:
        logger.warning(f"Mã {price_data['symbol']} chưa có trong DB.")
        return False

    try:
        PriceSnapshot.objects.create(
            stock=stock,
            reference_price=price_data.get("reference_price", Decimal("0")),
            ceiling_price=price_data.get("ceiling_price", Decimal("0")),
            floor_price=price_data.get("floor_price", Decimal("0")),
            current_price=price_data["current_price"],
            open_price=price_data.get("open_price"),
            high_price=price_data.get("high_price"),
            low_price=price_data.get("low_price"),
            volume=price_data.get("volume", 0),
            value=price_data.get("value", Decimal("0")),
            change=price_data.get("change", Decimal("0")),
            change_percent=price_data.get("change_percent", Decimal("0")),
            bid_price_1=price_data.get("bid_price_1"),
            bid_vol_1=price_data.get("bid_vol_1"),
            bid_price_2=price_data.get("bid_price_2"),
            bid_vol_2=price_data.get("bid_vol_2"),
            bid_price_3=price_data.get("bid_price_3"),
            bid_vol_3=price_data.get("bid_vol_3"),
            ask_price_1=price_data.get("ask_price_1"),
            ask_vol_1=price_data.get("ask_vol_1"),
            ask_price_2=price_data.get("ask_price_2"),
            ask_vol_2=price_data.get("ask_vol_2"),
            ask_price_3=price_data.get("ask_price_3"),
            ask_vol_3=price_data.get("ask_vol_3"),
        )
        return True
    except Exception as e:
        logger.error(f"Lỗi lưu snapshot {price_data['symbol']}: {e}")
        return False
