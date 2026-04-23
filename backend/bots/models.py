from django.db import models


class BotAnalysis(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    market_outlook = models.CharField(max_length=20, default="NEUTRAL")
    summary = models.TextField()
    evaluations = models.JSONField(default=list)
    best_strategy = models.CharField(max_length=300, blank=True)
    warning = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Analysis {self.created_at:%Y-%m-%d %H:%M} [{self.market_outlook}]"


class BotDailySnapshot(models.Model):
    """Snapshot P&L mỗi bot cuối mỗi ngày — dùng để tổng hợp 7 ngày."""
    date = models.DateField()
    bot_username = models.CharField(max_length=50)
    display_name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    total_value = models.BigIntegerField()   # VNĐ
    pnl_pct = models.FloatField()
    matched_orders = models.IntegerField(default=0)
    trades_today = models.IntegerField(default=0)  # số lệnh đặt trong ngày

    class Meta:
        unique_together = [("date", "bot_username")]
        ordering = ["-date", "-pnl_pct"]

    def __str__(self):
        return f"{self.date} | {self.display_name} | {self.pnl_pct:+.2f}%"
