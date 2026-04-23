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


def ensure_all_stocks_exist():
    """Lấy danh sách từ API và đẩy toàn bộ mã trên 3 sàn vào Database."""
    from market_data.models import Stock
    from .vnstock_client import get_all_market_symbols
    
    symbols_data = get_all_market_symbols()
    count = 0
    
    for row in symbols_data:
        ticker = row.get('ticker')
        exchange = row.get('comGroupCode')
        name = row.get('organName')
        
        if ticker:
            # Tạo mới hoặc cập nhật nếu đã có
            Stock.objects.get_or_create(
                symbol=ticker,
                defaults={
                    "company_name": name,
                    "exchange": exchange,
                    "is_vn30": ticker in VN30_SYMBOLS, # Tự động đánh dấu nếu thuộc rổ VN30
                    "is_active": True,
                }
            )
            count += 1
            
    logger.info(f"Đã nạp {count} mã cổ phiếu vào DB.")
    return count


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
        _broadcast_price(price_data)
        _trigger_matching(price_data["symbol"])
        return True
    except Exception as e:
        logger.error(f"Lỗi lưu snapshot {price_data['symbol']}: {e}")
        return False


def _trigger_matching(symbol: str):
    """Sau khi có giá mới, thử khớp tất cả lệnh đang chờ của mã này."""
    try:
        from trading.models import Order
        from trading.services.matching_engine import try_match_order

        pending = Order.objects.filter(
            stock__symbol=symbol,
            status__in=("PENDING", "PARTIAL"),
        ).select_related("stock", "user")

        for order in pending:
            try_match_order(order)
    except Exception as e:
        logger.debug(f"Trigger matching skip {symbol}: {e}")


def _broadcast_price(price_data: dict):
    """Broadcast giá mới xuống WebSocket clients."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        symbol = price_data["symbol"]
        payload = {k: str(v) if v is not None else None for k, v in price_data.items()}
        async_to_sync(channel_layer.group_send)(
            f"market_{symbol}",
            {"type": "price_update", "data": payload},
        )
    except Exception as e:
        logger.debug(f"Broadcast skip {price_data.get('symbol')}: {e}")