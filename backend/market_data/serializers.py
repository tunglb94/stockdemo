from rest_framework import serializers
from .models import Stock, PriceSnapshot


class PriceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceSnapshot
        fields = [
            "reference_price", "ceiling_price", "floor_price",
            "current_price", "open_price", "high_price", "low_price",
            "volume", "value", "change", "change_percent",
            "bid_price_1", "bid_vol_1", "bid_price_2", "bid_vol_2", "bid_price_3", "bid_vol_3",
            "ask_price_1", "ask_vol_1", "ask_price_2", "ask_vol_2", "ask_price_3", "ask_vol_3",
            "timestamp",
        ]


class StockSerializer(serializers.ModelSerializer):
    latest_price = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = ["id", "symbol", "company_name", "exchange", "industry", "is_vn30", "latest_price"]

    def get_latest_price(self, obj):
        try:
            snapshot = obj.snapshots.latest("timestamp")
            return PriceSnapshotSerializer(snapshot).data
        except Exception:
            return None


class StockDetailSerializer(StockSerializer):
    """Chi tiết mã CK kèm 5 snapshot gần nhất."""
    recent_prices = serializers.SerializerMethodField()

    class Meta(StockSerializer.Meta):
        fields = StockSerializer.Meta.fields + ["recent_prices"]

    def get_recent_prices(self, obj):
        snapshots = obj.snapshots.all()[:5]
        return PriceSnapshotSerializer(snapshots, many=True).data
