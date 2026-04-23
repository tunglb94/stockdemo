"""
Chạy tất cả bot AI một lần — mỗi bot phân tích thị trường và đặt lệnh.
Sau khi tất cả bot xong, Hermes3 Analyst đánh giá và lưu nhận xét vào DB.
"""
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Chay tat ca AI bot trader mot lan, sau do Hermes3 phan tich ket qua"

    def add_arguments(self, parser):
        parser.add_argument("--bot", type=str, default=None,
                            help="Chi chay 1 bot cu the (username)")
        parser.add_argument("--no-analyst", action="store_true",
                            help="Bo qua buoc Hermes3 analyst")

    def handle(self, *args, **options):
        from bots.definitions import BOTS
        from bots.ollama_client import ask_llm
        from bots.market_context import build_market_context, get_portfolio_state
        from bots.executor import execute_decisions
        from accounts.models import Wallet
        from decimal import Decimal

        target = options.get("bot")
        no_analyst = options.get("no_analyst", False)
        bots = [b for b in BOTS if target is None or b["username"] == target]

        ts = datetime.now().strftime("%H:%M:%S")
        self.stdout.write(f"\n[{ts}] Chay {len(bots)} bot AI...")

        START_CAPITAL = Decimal("100000000")
        analyst_inputs = []  # Thu thap de truyen cho Hermes

        for bot_def in bots:
            self.stdout.write(f"  >> {bot_def['display_name']} ({bot_def['model']})")

            try:
                user = User.objects.get(email=bot_def["email"])
                wallet = Wallet.objects.get(user=user)
            except Exception:
                self.stdout.write("  Bot chua duoc tao. Chay: python manage.py create_bots")
                continue

            portfolio = get_portfolio_state(user)
            context = build_market_context(portfolio, wallet.balance)

            result = ask_llm(
                model=bot_def["model"],
                system_prompt=bot_def["system_prompt"],
                user_message=context,
            )

            if not result:
                self.stdout.write(f"  LLM khong tra loi duoc")
                analyst_inputs.append(_make_analyst_input(
                    bot_def, wallet, portfolio, decisions=[], START_CAPITAL=START_CAPITAL
                ))
                continue

            decisions = result.get("decisions", [])
            analysis = result.get("analysis", "")
            self.stdout.write(f"  {len(decisions)} lenh | {analysis[:80]}")

            if decisions:
                logs = execute_decisions(user, decisions, portfolio)
                for log in logs:
                    self.stdout.write(log)
            else:
                self.stdout.write("  HOLD — khong giao dich vong nay")

            # Reload wallet sau khi execute
            wallet.refresh_from_db()
            analyst_inputs.append(_make_analyst_input(
                bot_def, wallet, portfolio, decisions, START_CAPITAL
            ))

        self.stdout.write(f"  Hoan thanh vong giao dich.")

        # Hermes3 Analyst — chay sau tat ca bot
        if not no_analyst and len(analyst_inputs) >= 1:
            self.stdout.write(f"\n  [Hermes3] Dang phan tich ket qua...")
            try:
                from bots.analyst import run_analyst
                ok = run_analyst(analyst_inputs)
                if ok:
                    self.stdout.write("  [Hermes3] Da luu nhan xet.")
                else:
                    self.stdout.write("  [Hermes3] Khong phan tich duoc (kiem tra Ollama).")
            except Exception as e:
                self.stdout.write(f"  [Hermes3] Loi: {e}")


def _make_analyst_input(bot_def, wallet, portfolio, decisions, START_CAPITAL):
    """Dong goi du lieu 1 bot cho Hermes analyst."""
    from market_data.models import Stock
    from decimal import Decimal

    # Tinh stock value tu portfolio
    stock_value = Decimal("0")
    holdings_list = []
    for sym, pos in portfolio.items():
        cur = Decimal(str(pos["current_price"]))
        stock_value += cur * pos["quantity"]
        holdings_list.append(sym)

    total = wallet.balance + wallet.frozen_balance + stock_value
    pnl = total - START_CAPITAL
    pnl_pct = float(pnl / START_CAPITAL * 100)

    return {
        "display_name": bot_def["display_name"],
        "model": bot_def["model"],
        "strategy_short": bot_def["system_prompt"].split("\n")[0][:80],
        "total_value": float(total),
        "cash": float(wallet.balance),
        "pnl_pct": round(pnl_pct, 2),
        "holdings": holdings_list,
        "decisions_this_round": [
            {
                "action": d.get("action", ""),
                "symbol": d.get("symbol", ""),
                "quantity": d.get("quantity", 0),
                "reason": d.get("reason", "")[:60],
            }
            for d in (decisions or [])
            if d.get("action") in ("BUY", "SELL")
        ],
    }
