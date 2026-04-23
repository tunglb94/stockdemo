from django.urls import path
from .views import (
    CryptoMarketView, CryptoPortfolioView, CryptoTradeView,
    CryptoBotLeaderboardView, FuturesBotLeaderboardView,
)

urlpatterns = [
    path("market/", CryptoMarketView.as_view()),
    path("portfolio/", CryptoPortfolioView.as_view()),
    path("trade/", CryptoTradeView.as_view()),
    path("bots/", CryptoBotLeaderboardView.as_view()),
    path("futures/bots/", FuturesBotLeaderboardView.as_view()),
]
