import logging
from celery import shared_task
from .services.vnstock_client import fetch_all_vn30_prices, fetch_current_price
from .services.data_processor import save_price_snapshot, ensure_vn30_stocks_exist

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_and_update_market_data(self):
    """Fetch giá tất cả mã VN30 và lưu vào DB. Chạy mỗi 5 phút."""
    try:
        ensure_vn30_stocks_exist()
        prices = fetch_all_vn30_prices()

        success_count = 0
        for price_data in prices:
            if save_price_snapshot(price_data):
                success_count += 1

        logger.info(f"Cập nhật xong {success_count}/{len(prices)} mã VN30.")
        return {"updated": success_count, "total": len(prices)}

    except Exception as exc:
        logger.error(f"Lỗi fetch market data: {exc}")
        raise self.retry(exc=exc)


@shared_task
def fetch_single_stock(symbol: str):
    """Fetch giá một mã cụ thể (trigger thủ công hoặc khi user xem chi tiết)."""
    price_data = fetch_current_price(symbol)
    if price_data:
        save_price_snapshot(price_data)
        return {"status": "ok", "symbol": symbol}
    return {"status": "error", "symbol": symbol}
