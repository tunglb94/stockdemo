from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Wallet


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["email", "username", "is_active", "created_at"]
    list_filter = ["is_active", "is_staff"]
    search_fields = ["email", "username"]
    ordering = ["-created_at"]
    fieldsets = UserAdmin.fieldsets + (
        ("Thông tin bổ sung", {"fields": ("phone", "avatar")}),
    )


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["user", "balance", "frozen_balance", "available_balance", "updated_at"]
    search_fields = ["user__email"]
    readonly_fields = ["available_balance"]
