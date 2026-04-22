import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def process_t_plus_settlement():
    """Chạy mỗi sáng T+2 settlement."""
    from trading.services.settlement import process_t_plus_settlement as _settle
    count = _settle()
    return {"released": count}


@shared_task
def match_pending_orders():
    """Thử khớp lại tất cả lệnh đang chờ (chạy mỗi 5 phút trong giờ giao dịch)."""
    from trading.models import Order
    from trading.services.matching_engine import try_match_order

    pending = Order.objects.filter(status__in=["PENDING", "PARTIAL"]).select_related("stock", "user")
    matched = sum(1 for order in pending if try_match_order(order))
    logger.info(f"Re-match: {matched}/{pending.count()} lệnh khớp.")
    return {"matched": matched}


@shared_task
def update_leaderboard():
    """Tính và cache bảng xếp hạng user theo tổng tài sản."""
    from django.contrib.auth import get_user_model
    from trading.services.pnl_calculator import get_portfolio_summary
    from django.core.cache import cache

    User = get_user_model()
    rankings = []

    for user in User.objects.filter(is_active=True, is_staff=False):
        try:
            summary = get_portfolio_summary(user)
            rankings.append({
                "username": user.username,
                "email": user.email,
                "total_assets": float(summary["total_assets"]),
                "total_pnl": float(summary["total_pnl"]),
                "total_pnl_percent": float(summary["total_pnl_percent"]),
            })
        except Exception:
            continue

    rankings.sort(key=lambda x: x["total_assets"], reverse=True)
    cache.set("leaderboard", rankings[:50], timeout=1800)
    logger.info(f"Cập nhật leaderboard: {len(rankings)} users.")
    return {"count": len(rankings)}
