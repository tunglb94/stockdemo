from django.db import models


class BotAnalysis(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    market_outlook = models.CharField(max_length=20, default="NEUTRAL")  # BULLISH/BEARISH/NEUTRAL
    summary = models.TextField()
    evaluations = models.JSONField(default=list)   # [{bot, verdict, score, comment}]
    best_strategy = models.CharField(max_length=300, blank=True)
    warning = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Analysis {self.created_at:%Y-%m-%d %H:%M} [{self.market_outlook}]"
