from django.db import models
from django.conf import settings


class CryptoAsset(models.Model):
    CATEGORY_CHOICES = [("CRYPTO", "Cryptocurrency"), ("COMMODITY", "Commodity")]

    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="CRYPTO")
    coingecko_id = models.CharField(max_length=100, blank=True)
    yfinance_ticker = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    rank = models.IntegerField(default=999)

    class Meta:
        ordering = ["rank"]

    def __str__(self):
        return self.symbol


class CryptoSnapshot(models.Model):
    asset = models.ForeignKey(CryptoAsset, on_delete=models.CASCADE, related_name="snapshots")
    price_usd = models.DecimalField(max_digits=20, decimal_places=8)
    change_24h = models.FloatField(default=0)
    volume_24h = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        get_latest_by = "timestamp"


class CryptoWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crypto_wallet"
    )
    balance_usd = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    frozen_usd = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    @property
    def available(self):
        return self.balance_usd - self.frozen_usd


class CryptoPortfolio(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crypto_portfolio"
    )
    asset = models.ForeignKey(CryptoAsset, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    avg_cost_usd = models.DecimalField(max_digits=20, decimal_places=8)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "asset")]


class CryptoOrder(models.Model):
    SIDE_CHOICES = [("BUY", "Buy"), ("SELL", "Sell")]
    STATUS_CHOICES = [("MATCHED", "Matched"), ("CANCELLED", "Cancelled")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="crypto_orders"
    )
    asset = models.ForeignKey(CryptoAsset, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    price_usd = models.DecimalField(max_digits=20, decimal_places=8)
    total_usd = models.DecimalField(max_digits=20, decimal_places=4)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="MATCHED")
    created_at = models.DateTimeField(auto_now_add=True)

    # Lưu reasoning + PnL để Qwen analyze sau
    bot_reasoning = models.TextField(blank=True, default="")
    cost_basis_usd = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    pnl_usd = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def pnl_pct(self):
        if self.side == "SELL" and self.cost_basis_usd and self.cost_basis_usd > 0:
            return float((self.price_usd - self.cost_basis_usd) / self.cost_basis_usd * 100)
        return None


class BotRoundLog(models.Model):
    """Lưu analysis text của LLM mỗi vòng chạy — không cần gọi thêm LLM."""
    bot_username = models.CharField(max_length=50)
    analysis_text = models.TextField(blank=True, default="")
    decisions_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class TradeAnalysis(models.Model):
    """Kết quả Qwen 3.5 phân tích sâu một lệnh cụ thể — lưu cache để không gọi lại."""
    order = models.OneToOneField(CryptoOrder, on_delete=models.CASCADE, related_name="analysis")
    analysis_text = models.TextField()
    quality_score = models.FloatField(default=0.0)  # 0.0 – 1.0
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class FuturesTradeAnalysis(models.Model):
    """Cache kết quả phân tích Qwen cho 1 FuturesPosition — tránh gọi LLM lại."""
    position = models.OneToOneField("FuturesPosition", on_delete=models.CASCADE, related_name="analysis")
    analysis_text = models.TextField()
    quality_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class LearnedLesson(models.Model):
    """Bài học rút ra từ trade tốt/xấu, được inject vào context các bot sau."""
    POLARITY_CHOICES = [("GOOD", "Good"), ("WARNING", "Warning")]

    source_order = models.ForeignKey(
        CryptoOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name="lessons"
    )
    source_bot = models.CharField(max_length=50)
    lesson_text = models.TextField()
    polarity = models.CharField(max_length=10, choices=POLARITY_CHOICES, default="GOOD")
    tags = models.CharField(max_length=200, blank=True, default="universal")
    quality_score = models.FloatField(default=0.5)
    pnl_at_extraction = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-quality_score", "-created_at"]

    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


# ── FUTURES / LONG-SHORT ──────────────────────────────────────────────────────

class FuturesWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="futures_wallet"
    )
    balance_usd = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    used_margin_usd = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    @property
    def available(self):
        return self.balance_usd - self.used_margin_usd


class FuturesPosition(models.Model):
    DIRECTION_CHOICES = [("LONG", "Long"), ("SHORT", "Short")]
    STATUS_CHOICES = [("OPEN", "Open"), ("CLOSED", "Closed"), ("LIQUIDATED", "Liquidated")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="futures_positions"
    )
    asset = models.ForeignKey(CryptoAsset, on_delete=models.CASCADE)
    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)   # asset units
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    margin_usd = models.DecimalField(max_digits=20, decimal_places=4)  # USD locked
    leverage = models.IntegerField(default=1)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="OPEN")
    realized_pnl = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    bot_reasoning = models.TextField(blank=True, default="")
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-opened_at"]

    @property
    def notional_usd(self):
        return self.margin_usd * self.leverage

    def unrealized_pnl(self, current_price):
        from decimal import Decimal
        cur = Decimal(str(current_price))
        if self.direction == "LONG":
            return (cur - self.entry_price) * self.quantity
        else:
            return (self.entry_price - cur) * self.quantity

    def liq_price(self):
        """Liquidation at ~80% margin loss."""
        from decimal import Decimal
        liq_move = self.margin_usd * Decimal("0.8") / self.quantity
        if self.direction == "LONG":
            return float(self.entry_price - liq_move)
        else:
            return float(self.entry_price + liq_move)


class NewsItem(models.Model):
    CATEGORY_CHOICES = [
        ("CRYPTO", "Crypto"),
        ("MACRO", "Macro"),
        ("COMMODITY", "Commodity"),
        ("GENERAL", "General"),
    ]
    SENTIMENT_CHOICES = [("BULLISH", "Bullish"), ("BEARISH", "Bearish"), ("NEUTRAL", "Neutral")]

    title = models.TextField()
    summary = models.TextField(blank=True)
    source = models.CharField(max_length=100)
    url = models.URLField(max_length=500, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="CRYPTO")
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES, default="NEUTRAL")
    symbols = models.CharField(max_length=200, blank=True)  # comma-separated: "BTC,ETH"
    published_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        get_latest_by = "published_at"

    def __str__(self):
        return f"[{self.source}] {self.title[:60]}"


class FearGreedSnapshot(models.Model):
    value = models.IntegerField()          # 0-100
    label = models.CharField(max_length=30)  # "Extreme Fear", "Greed", etc.
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        get_latest_by = "timestamp"
