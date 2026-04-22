from rest_framework import serializers
from .models import Order, Portfolio, Transaction, TPlusRecord
from market_data.serializers import StockSerializer


class PlaceOrderSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    side = serializers.ChoiceField(choices=["BUY", "SELL"])
    order_type = serializers.ChoiceField(choices=["LO", "MP", "ATO", "ATC"])
    quantity = serializers.IntegerField(min_value=100)
    price = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True)

    def validate(self, attrs):
        if attrs["order_type"] == "LO" and not attrs.get("price"):
            raise serializers.ValidationError({"price": "Lệnh LO phải có giá đặt."})
        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["quantity", "price", "amount", "fee", "tax", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    stock_symbol = serializers.CharField(source="stock.symbol", read_only=True)
    stock_name = serializers.CharField(source="stock.company_name", read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)
    remaining_quantity = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = [
            "id", "stock_symbol", "stock_name", "order_type", "side",
            "quantity", "price", "matched_quantity", "matched_price",
            "remaining_quantity", "status", "reject_reason",
            "frozen_amount", "transactions", "created_at", "updated_at",
        ]


class HoldingSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="stock.symbol", read_only=True)
    company_name = serializers.CharField(source="stock.company_name", read_only=True)
    market_value = serializers.ReadOnlyField()
    unrealized_pnl = serializers.ReadOnlyField()

    class Meta:
        model = Portfolio
        fields = [
            "symbol", "company_name", "quantity", "available_quantity",
            "frozen_quantity", "avg_cost", "market_value", "unrealized_pnl",
        ]


class TPlusRecordSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="stock.symbol", read_only=True)

    class Meta:
        model = TPlusRecord
        fields = ["symbol", "quantity", "purchase_date", "available_date", "is_released"]
