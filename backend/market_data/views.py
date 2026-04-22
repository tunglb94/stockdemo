from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from .models import Stock, PriceSnapshot
from .serializers import StockSerializer, StockDetailSerializer, PriceSnapshotSerializer
from .tasks import fetch_single_stock
from .services.vnstock_client import fetch_stock_history


class StockListView(generics.ListAPIView):
    """Danh sách tất cả mã chứng khoán (ưu tiên VN30)."""
    serializer_class = StockSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Stock.objects.filter(is_active=True)
        vn30_only = self.request.query_params.get("vn30")
        if vn30_only:
            qs = qs.filter(is_vn30=True)
        return qs.prefetch_related("snapshots").order_by("-is_vn30", "symbol")


class StockDetailView(generics.RetrieveAPIView):
    """Chi tiết một mã chứng khoán."""
    serializer_class = StockDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "symbol"

    def get_object(self):
        symbol = self.kwargs["symbol"].upper()
        stock = get_object_or_404(Stock, symbol=symbol, is_active=True)
        # Trigger fetch ngay nếu user đang xem
        fetch_single_stock.delay(symbol)
        return stock


class StockHistoryView(APIView):
    """Lịch sử giá cho biểu đồ nến."""
    permission_classes = [AllowAny]

    def get(self, request, symbol):
        symbol = symbol.upper()
        start = request.query_params.get("start", "2024-01-01")
        end = request.query_params.get("end", "2025-12-31")
        interval = request.query_params.get("interval", "1D")
        data = fetch_stock_history(symbol, start, end, interval)
        return Response(data)


class MarketOverviewView(APIView):
    """Tổng quan thị trường: VN-Index, top tăng, top giảm."""
    permission_classes = [AllowAny]

    def get(self, request):
        stocks = Stock.objects.filter(is_active=True, is_vn30=True).prefetch_related("snapshots")
        result = []
        for stock in stocks:
            try:
                snapshot = stock.snapshots.latest("timestamp")
                result.append({
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,
                    "current_price": snapshot.current_price,
                    "change": snapshot.change,
                    "change_percent": snapshot.change_percent,
                    "volume": snapshot.volume,
                    "ceiling_price": snapshot.ceiling_price,
                    "floor_price": snapshot.floor_price,
                    "reference_price": snapshot.reference_price,
                })
            except PriceSnapshot.DoesNotExist:
                continue

        # Sắp xếp top tăng/giảm
        result.sort(key=lambda x: x["change_percent"], reverse=True)
        return Response({
            "vn30": result,
            "top_gainers": result[:5],
            "top_losers": result[-5:][::-1],
        })
