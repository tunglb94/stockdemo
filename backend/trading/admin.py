from django.contrib import admin
from .models import Order, Portfolio, Transaction, TPlusRecord


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "stock", "side", "order_type", "quantity", "price", "status", "created_at"]
    list_filter = ["side", "order_type", "status"]
    search_fields = ["user__email", "stock__symbol"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ["user", "stock", "quantity", "available_quantity", "frozen_quantity", "avg_cost"]
    search_fields = ["user__email", "stock__symbol"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["order", "quantity", "price", "amount", "fee", "tax", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(TPlusRecord)
class TPlusRecordAdmin(admin.ModelAdmin):
    list_display = ["user", "stock", "quantity", "purchase_date", "available_date", "is_released"]
    list_filter = ["is_released"]
    search_fields = ["user__email", "stock__symbol"]
