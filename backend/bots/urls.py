from django.urls import path
from .views import BotLeaderboardView, BotAnalysisView

urlpatterns = [
    path("leaderboard/", BotLeaderboardView.as_view()),
    path("analysis/", BotAnalysisView.as_view()),
]
