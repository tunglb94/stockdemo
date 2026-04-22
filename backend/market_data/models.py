from django.db import models


class Stock(models.Model):
    EXCHANGE_CHOICES = [
        ("HOSE", "HOSE"),
        ("HNX", "HNX"),
        ("UPCOM", "UPCOM"),
    ]

    symbol = models.CharField(max_length=10, unique=True, db_index=True)
    company_name = models.CharField(max_length=255)
    exchange = models.CharField(max_length=10, choices=EXCHANGE_CHOICES)
    industry = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_vn30 = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stocks"
        ordering = ["symbol"]

    def __str__(self):
        return f"{self.symbol} - {self.company_name}"


class PriceSnapshot(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="snapshots")
    reference_price = models.DecimalField(max_digits=15, decimal_places=2)
    ceiling_price = models.DecimalField(max_digits=15, decimal_places=2)
    floor_price = models.DecimalField(max_digits=15, decimal_places=2)
    current_price = models.DecimalField(max_digits=15, decimal_places=2)
    open_price = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    high_price = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    low_price = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    volume = models.BigIntegerField(default=0)
    value = models.DecimalField(max_digits=22, decimal_places=2, default=0)
    change = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    # Dư mua/dư bán top 3
    bid_price_1 = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    bid_vol_1 = models.BigIntegerField(null=True)
    bid_price_2 = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    bid_vol_2 = models.BigIntegerField(null=True)
    bid_price_3 = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    bid_vol_3 = models.BigIntegerField(null=True)
    ask_price_1 = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    ask_vol_1 = models.BigIntegerField(null=True)
    ask_price_2 = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    ask_vol_2 = models.BigIntegerField(null=True)
    ask_price_3 = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    ask_vol_3 = models.BigIntegerField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "price_snapshots"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["stock", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.stock.symbol} @ {self.current_price} ({self.timestamp})"


class MarketSession(models.Model):
    SESSION_TYPES = [
        ("ATO", "ATO 9:00-9:15"),
        ("CONTINUOUS", "Liên tục 9:15-11:30 / 13:00-14:30"),
        ("ATC", "ATC 14:30-14:45"),
        ("CLOSED", "Đóng cửa"),
    ]

    session_type = models.CharField(max_length=15, choices=SESSION_TYPES)
    date = models.DateField()
    is_trading_day = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "market_sessions"

    def __str__(self):
        return f"{self.date} - {self.session_type}"
