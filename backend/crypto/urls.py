from django.urls import path
from .views import (
    CryptoMarketView, CryptoPriceStreamView, CryptoPortfolioView,
    CryptoTradeView, CryptoBotLeaderboardView, FuturesBotLeaderboardView,
    FuturesCloseAllView, AnalyzeTradeView, AnalyzeFuturesTradeView,
)

urlpatterns = [
    path("market/",                        CryptoMarketView.as_view()),
    path("prices/stream/",                 CryptoPriceStreamView.as_view()),
    path("portfolio/",                     CryptoPortfolioView.as_view()),
    path("trade/",                         CryptoTradeView.as_view()),
    path("bots/",                          CryptoBotLeaderboardView.as_view()),
    path("bots/analyze-trade/<int:order_id>/", AnalyzeTradeView.as_view()),
    path("futures/bots/",                  FuturesBotLeaderboardView.as_view()),
    path("futures/close-all/",             FuturesCloseAllView.as_view()),
    path("futures/analyze-trade/<int:position_id>/", AnalyzeFuturesTradeView.as_view()),
]
