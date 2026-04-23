"""
Hiển thị bảng xếp hạng hiệu suất 5 bot AI.
Dùng: python manage.py bot_leaderboard
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()
START_CAPITAL = Decimal("50000000")


class Command(BaseCommand):
    help = "Bảng xếp hạng hiệu suất AI bot trader"

    def handle(self, *args, **options):
        from bots.definitions import BOTS
        from accounts.models import Wallet
        from trading.models import Portfolio
        from market_data.models import PriceSnapshot

        results = []

        for bot_def in BOTS:
            try:
                user = User.objects.get(email=bot_def["email"])
                wallet = Wallet.objects.get(user=user)
            except Exception:
                continue

            # Tổng giá trị danh mục
            portfolio_value = Decimal("0")
            for pos in Portfolio.objects.filter(user=user).select_related("stock"):
                try:
                    snap = pos.stock.snapshots.latest("timestamp")
                    portfolio_value += snap.current_price * pos.quantity
                except Exception:
                    portfolio_value += pos.avg_cost * pos.quantity

            total = wallet.balance + wallet.frozen_balance + portfolio_value
            pnl = total - START_CAPITAL
            pnl_pct = (pnl / START_CAPITAL * 100)

            # Số lệnh đã khớp
            from trading.models import Order
            matched = Order.objects.filter(user=user, status="MATCHED").count()
            pending = Order.objects.filter(user=user, status="PENDING").count()

            results.append({
                "name": bot_def["display_name"],
                "model": bot_def["model"],
                "total": total,
                "pnl": pnl,
                "pnl_pct": float(pnl_pct),
                "matched": matched,
                "pending": pending,
                "cash": wallet.balance,
                "stock_value": portfolio_value,
            })

        # Sắp xếp theo P&L
        results.sort(key=lambda x: x["pnl_pct"], reverse=True)

        self.stdout.write(f"\n{'='*70}")
        self.stdout.write("🏆 BẢNG XẾP HẠNG AI BOT TRADER")
        self.stdout.write(f"   Vốn ban đầu: {START_CAPITAL:,.0f} VNĐ / bot")
        self.stdout.write(f"{'='*70}\n")

        medals = ["🥇", "🥈", "🥉", "4️⃣ ", "5️⃣ "]
        for i, r in enumerate(results):
            sign = "+" if r["pnl"] >= 0 else ""
            color = self.style.SUCCESS if r["pnl"] >= 0 else self.style.ERROR
            self.stdout.write(
                f"{medals[i]} {r['name']:<25} ({r['model'][:15]})"
            )
            self.stdout.write(
                f"   Tổng tài sản: {r['total']:>15,.0f}đ"
            )
            self.stdout.write(color(
                f"   P&L: {sign}{r['pnl']:>14,.0f}đ  ({sign}{r['pnl_pct']:.2f}%)"
            ))
            self.stdout.write(
                f"   Tiền mặt: {r['cash']:>13,.0f}đ  |  Cổ phiếu: {r['stock_value']:>12,.0f}đ"
            )
            self.stdout.write(
                f"   Lệnh khớp: {r['matched']}  |  Đang chờ: {r['pending']}\n"
            )

        self.stdout.write(f"{'='*70}\n")
