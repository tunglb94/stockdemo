"""
Tính lãi/lỗ danh mục đầu tư.
"""
from decimal import Decimal
from trading.models import Portfolio, Transaction
from accounts.models import Wallet
from market_data.models import PriceSnapshot


def get_portfolio_summary(user) -> dict:
    """Tổng hợp danh mục: tổng tài sản, lãi/lỗ, tỉ lệ."""
    portfolios = Portfolio.objects.filter(user=user).select_related("stock")

    total_cost = Decimal("0")
    total_market_value = Decimal("0")
    holdings = []

    for p in portfolios:
        try:
            snapshot = p.stock.snapshots.latest("timestamp")
            current_price = snapshot.current_price
        except PriceSnapshot.DoesNotExist:
            current_price = p.avg_cost

        cost = p.quantity * p.avg_cost
        market_val = p.quantity * current_price
        pnl = market_val - cost
        pnl_percent = (pnl / cost * 100) if cost else Decimal("0")

        total_cost += cost
        total_market_value += market_val

        holdings.append({
            "symbol": p.stock.symbol,
            "company_name": p.stock.company_name,
            "quantity": p.quantity,
            "available_quantity": p.available_quantity,
            "frozen_quantity": p.frozen_quantity,
            "avg_cost": p.avg_cost,
            "current_price": current_price,
            "market_value": market_val,
            "cost_value": cost,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
        })

    wallet = Wallet.objects.get(user=user)
    total_assets = wallet.balance + total_market_value
    total_pnl = total_market_value - total_cost

    return {
        "wallet": {
            "balance": wallet.balance,
            "frozen_balance": wallet.frozen_balance,
            "available_balance": wallet.available_balance,
        },
        "holdings": holdings,
        "total_cost": total_cost,
        "total_market_value": total_market_value,
        "total_assets": total_assets,
        "total_pnl": total_pnl,
        "total_pnl_percent": (total_pnl / total_cost * 100) if total_cost else Decimal("0"),
    }


def get_trading_history_summary(user) -> dict:
    """Thống kê giao dịch: tổng lệnh, thắng/thua, lãi thực hiện."""
    from trading.models import Order
    orders = Order.objects.filter(user=user, status="MATCHED").select_related("stock")
    total_orders = orders.count()
    total_buy = orders.filter(side="BUY").count()
    total_sell = orders.filter(side="SELL").count()

    realized_pnl = Decimal("0")
    for order in orders.filter(side="SELL"):
        for tx in order.transactions.all():
            realized_pnl += tx.amount - tx.fee - tx.tax

    return {
        "total_orders": total_orders,
        "total_buy": total_buy,
        "total_sell": total_sell,
        "realized_pnl": realized_pnl,
    }
