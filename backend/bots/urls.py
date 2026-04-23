from django.urls import path
from .views import BotLeaderboardView, BotAnalysisView, BotHistoryView

urlpatterns = [
    path("leaderboard/", BotLeaderboardView.as_view()),
    path("analysis/", BotAnalysisView.as_view()),
    path("history/", BotHistoryView.as_view()),
]
