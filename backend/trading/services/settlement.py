"""
T+2 Settlement: mỗi sáng, release cổ phiếu đã đủ T+2 ngày.
"""
import logging
from datetime import date
from django.db import transaction
from trading.models import TPlusRecord, Portfolio

logger = logging.getLogger(__name__)


def process_t_plus_settlement():
    """
    Release cổ phiếu từ TPlusRecord đến hạn hôm nay.
    Chạy mỗi sáng lúc 9:00 (trước phiên ATO).
    """
    today = date.today()
    records = TPlusRecord.objects.select_related("user", "stock").filter(
        available_date__lte=today,
        is_released=False,
    )

    released_count = 0
    for record in records:
        try:
            with transaction.atomic():
                portfolio = Portfolio.objects.select_for_update().filter(
                    user=record.user,
                    stock=record.stock,
                ).first()

                if portfolio:
                    portfolio.available_quantity += record.quantity
                    portfolio.save(update_fields=["available_quantity", "updated_at"])

                record.is_released = True
                record.save(update_fields=["is_released"])
                released_count += 1

                logger.info(
                    f"T+ released: {record.user.email} | "
                    f"{record.stock.symbol} x{record.quantity}"
                )
        except Exception as e:
            logger.error(f"Lỗi release T+ record {record.id}: {e}")

    logger.info(f"Settlement xong: {released_count} records được release.")
    return released_count
