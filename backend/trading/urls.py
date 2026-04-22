from django.urls import path
from .views import (
    PlaceOrderView, CancelOrderView, OrderListView,
    PortfolioView, HoldingListView, TPlusView, TradingStatsView,
)

urlpatterns = [
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/place/", PlaceOrderView.as_view(), name="order-place"),
    path("orders/<uuid:order_id>/cancel/", CancelOrderView.as_view(), name="order-cancel"),
    path("portfolio/", PortfolioView.as_view(), name="portfolio"),
    path("holdings/", HoldingListView.as_view(), name="holdings"),
    path("t-plus/", TPlusView.as_view(), name="t-plus"),
    path("stats/", TradingStatsView.as_view(), name="trading-stats"),
]
