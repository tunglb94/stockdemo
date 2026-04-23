from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model

User = get_user_model()
START_CAPITAL = Decimal("100000000")


class BotLeaderboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from bots.definitions import BOTS
        from accounts.models import Wallet
        from trading.models import Portfolio, Order

        results = []
        for bot_def in BOTS:
            try:
                user = User.objects.get(email=bot_def["email"])
                wallet = Wallet.objects.get(user=user)
            except Exception:
                continue

            # Tổng giá trị cổ phiếu đang giữ
            stock_value = Decimal("0")
            holdings = []
            for pos in Portfolio.objects.filter(user=user).select_related("stock"):
                try:
                    snap = pos.stock.snapshots.latest("timestamp")
                    cur = snap.current_price
                except Exception:
                    cur = pos.avg_cost
                stock_value += cur * pos.quantity
                pnl_pct = float((cur - pos.avg_cost) / pos.avg_cost * 100) if pos.avg_cost else 0
                holdings.append({
                    "symbol": pos.stock.symbol,
                    "quantity": pos.quantity,
                    "available": pos.available_quantity,
                    "avg_cost": float(pos.avg_cost),
                    "current_price": float(cur),
                    "pnl_pct": round(pnl_pct, 2),
                })

            total = wallet.balance + wallet.frozen_balance + stock_value
            pnl = total - START_CAPITAL
            pnl_pct = float(pnl / START_CAPITAL * 100)

            recent_orders = Order.objects.filter(
                user=user
            ).select_related("stock").order_by("-created_at")[:5]

            results.append({
                "username": bot_def["username"],
                "display_name": bot_def["display_name"],
                "model": bot_def["model"],
                "strategy": bot_def["system_prompt"][:80] + "...",
                "total_value": float(total),
                "cash": float(wallet.balance),
                "stock_value": float(stock_value),
                "pnl": float(pnl),
                "pnl_pct": round(pnl_pct, 2),
                "holdings": sorted(holdings, key=lambda x: -abs(x["pnl_pct"])),
                "matched_orders": Order.objects.filter(user=user, status="MATCHED").count(),
                "pending_orders": Order.objects.filter(user=user, status="PENDING").count(),
                "recent_orders": [
                    {
                        "symbol": o.stock.symbol,
                        "side": o.side,
                        "quantity": o.quantity,
                        "price": float(o.matched_price or o.price or 0),
                        "status": o.status,
                        "created_at": o.created_at.strftime("%d/%m %H:%M"),
                    }
                    for o in recent_orders
                ],
            })

        results.sort(key=lambda x: -x["pnl_pct"])
        return Response(results)


class BotAnalysisView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from bots.models import BotAnalysis
        try:
            latest = BotAnalysis.objects.first()
            if not latest:
                return Response(None)
            return Response({
                "created_at": latest.created_at.strftime("%d/%m %H:%M"),
                "market_outlook": latest.market_outlook,
                "summary": latest.summary,
                "evaluations": latest.evaluations,
                "best_strategy": latest.best_strategy,
                "warning": latest.warning,
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)
