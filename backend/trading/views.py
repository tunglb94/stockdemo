from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Order, Portfolio, TPlusRecord
from .serializers import (
    PlaceOrderSerializer, OrderSerializer, HoldingSerializer,
    TPlusRecordSerializer,
)
from .services.order_service import validate_and_place_order, cancel_order
from .services.matching_engine import try_match_order
from .services.pnl_calculator import get_portfolio_summary, get_trading_history_summary


class PlaceOrderView(APIView):
    """Đặt lệnh mua hoặc bán."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = validate_and_place_order(request.user, serializer.validated_data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Lỗi hệ thống, vui lòng thử lại."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Thử khớp lệnh ngay
        try_match_order(order)
        order.refresh_from_db()

        return Response(
            {
                "message": "Đặt lệnh thành công.",
                "order": OrderSerializer(order).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CancelOrderView(APIView):
    """Hủy lệnh chờ."""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        try:
            cancel_order(request.user, order)
            return Response({"message": "Hủy lệnh thành công."})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrderListView(generics.ListAPIView):
    """Lịch sử lệnh của user."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Order.objects.filter(user=self.request.user).select_related("stock").prefetch_related("transactions")
        status_filter = self.request.query_params.get("status")
        side_filter = self.request.query_params.get("side")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if side_filter:
            qs = qs.filter(side=side_filter.upper())
        return qs


class PortfolioView(APIView):
    """Danh mục đầu tư và P/L tổng hợp."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        summary = get_portfolio_summary(request.user)
        return Response(summary)


class HoldingListView(generics.ListAPIView):
    """Danh sách cổ phiếu đang nắm giữ."""
    serializer_class = HoldingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user, quantity__gt=0).select_related("stock")


class TPlusView(generics.ListAPIView):
    """Xem cổ phiếu đang trong giai đoạn T+2."""
    serializer_class = TPlusRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TPlusRecord.objects.filter(user=self.request.user, is_released=False).select_related("stock")


class TradingStatsView(APIView):
    """Thống kê giao dịch của user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_trading_history_summary(request.user))
