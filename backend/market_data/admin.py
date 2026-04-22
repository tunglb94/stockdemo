from django.contrib import admin
from .models import Stock, PriceSnapshot


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ["symbol", "company_name", "exchange", "is_vn30", "is_active"]
    list_filter = ["exchange", "is_vn30", "is_active"]
    search_fields = ["symbol", "company_name"]


@admin.register(PriceSnapshot)
class PriceSnapshotAdmin(admin.ModelAdmin):
    list_display = ["stock", "current_price", "change_percent", "volume", "timestamp"]
    list_filter = ["stock"]
    readonly_fields = [f.name for f in PriceSnapshot._meta.fields]
