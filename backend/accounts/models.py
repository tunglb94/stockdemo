from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    frozen_balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallets"

    @property
    def available_balance(self):
        return self.balance - self.frozen_balance

    def freeze(self, amount: Decimal):
        """Giam tiền khi đặt lệnh mua."""
        if amount > self.available_balance:
            raise ValueError("Số dư khả dụng không đủ")
        self.frozen_balance += amount
        self.save(update_fields=["frozen_balance", "updated_at"])

    def unfreeze(self, amount: Decimal):
        """Giải phóng tiền bị giam (khi hủy lệnh)."""
        self.frozen_balance = max(Decimal("0"), self.frozen_balance - amount)
        self.save(update_fields=["frozen_balance", "updated_at"])

    def deduct(self, amount: Decimal):
        """Trừ tiền thật sau khi lệnh khớp (từ phần frozen)."""
        self.balance -= amount
        self.frozen_balance -= amount
        self.save(update_fields=["balance", "frozen_balance", "updated_at"])

    def deposit(self, amount: Decimal):
        """Cộng tiền (sau khi bán cổ phiếu)."""
        self.balance += amount
        self.save(update_fields=["balance", "updated_at"])

    def __str__(self):
        return f"Wallet({self.user.email}) - {self.balance:,.0f} VNĐ"
