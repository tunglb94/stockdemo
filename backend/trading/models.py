import uuid
from django.db import models
from accounts.models import User
from market_data.models import Stock


class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ("LO", "Lệnh giới hạn"),
        ("MP", "Lệnh thị trường"),
        ("ATO", "ATO"),
        ("ATC", "ATC"),
    ]
    SIDE_CHOICES = [
        ("BUY", "Mua"),
        ("SELL", "Bán"),
    ]
    STATUS_CHOICES = [
        ("PENDING", "Chờ khớp"),
        ("MATCHED", "Đã khớp toàn phần"),
        ("PARTIAL", "Khớp một phần"),
        ("CANCELLED", "Đã hủy"),
        ("REJECTED", "Bị từ chối"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=5, choices=ORDER_TYPE_CHOICES)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    matched_quantity = models.IntegerField(default=0)
    matched_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    frozen_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    reject_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    @property
    def remaining_quantity(self):
        return self.quantity - self.matched_quantity

    def __str__(self):
        return f"{self.side} {self.quantity} {self.stock.symbol} @ {self.price}"


class Portfolio(models.Model):
    """Cổ phiếu đang nắm giữ."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="portfolio")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    available_quantity = models.IntegerField(default=0)  # Có thể bán ngay (T+0/T+2 đã qua)
    frozen_quantity = models.IntegerField(default=0)      # Đang chờ lệnh bán khớp
    avg_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portfolios"
        unique_together = ["user", "stock"]

    @property
    def market_value(self):
        try:
            snapshot = self.stock.snapshots.latest("timestamp")
            return self.quantity * snapshot.current_price
        except Exception:
            return self.quantity * self.avg_cost

    @property
    def unrealized_pnl(self):
        cost = self.quantity * self.avg_cost
        return self.market_value - cost

    def __str__(self):
        return f"{self.user.email} | {self.stock.symbol} x{self.quantity}"


class Transaction(models.Model):
    """Lịch sử lệnh đã khớp thành công."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="transactions")
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-created_at"]


class TPlusRecord(models.Model):
    """Theo dõi cổ phiếu đang trong giai đoạn T+2 chưa được bán."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="t_plus_records")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    purchase_date = models.DateField()
    available_date = models.DateField()  # Ngày được phép bán
    is_released = models.BooleanField(default=False)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "t_plus_records"
        ordering = ["available_date"]

    def __str__(self):
        return f"{self.user.email} | {self.stock.symbol} x{self.quantity} - available {self.available_date}"
