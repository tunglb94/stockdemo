import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Chay futures bot AI (long/short) mot vong"

    def add_arguments(self, parser):
        parser.add_argument("--bot", type=str, default=None)

    def handle(self, *args, **options):
        from crypto.bots.futures_definitions import FUTURES_BOTS
        from crypto.bots.futures_context import build_futures_context
        from crypto.bots.futures_executor import get_futures_portfolio_state
        from crypto.bots.futures_executor import execute_futures_decisions
        from crypto.models import FuturesWallet
        from bots.ollama_client import ask_llm

        target = options.get("bot")
        bots = [b for b in FUTURES_BOTS if target is None or b["username"] == target]

        ts = datetime.now().strftime("%H:%M:%S")
        self.stdout.write(f"\n[{ts}] Futures: chay {len(bots)} bot...")

        for bot_def in bots:
            self.stdout.write(f"  >> {bot_def['display_name']} ({bot_def['model']})")

            try:
                user = User.objects.get(email=bot_def["email"])
                wallet = FuturesWallet.objects.get(user=user)
            except Exception:
                self.stdout.write("  Bot chua duoc tao. Chay: python manage.py create_futures_bots")
                continue

            positions = get_futures_portfolio_state(user)
            context = build_futures_context(positions, wallet.balance_usd)

            result = ask_llm(
                model=bot_def["model"],
                system_prompt=bot_def["system_prompt"],
                user_message=context,
                append_json_instruction=False,
            )

            if not result:
                self.stdout.write("  LLM khong tra loi")
                continue

            decisions = result.get("decisions", [])
            analysis = result.get("analysis", "").encode("ascii", errors="replace").decode("ascii")
            self.stdout.write(f"  {len(decisions)} quyet dinh | {analysis[:80]}")

            if decisions:
                logs = execute_futures_decisions(user, decisions)
                for log in logs:
                    self.stdout.write(log.encode("ascii", errors="replace").decode("ascii"))
            else:
                self.stdout.write("  HOLD - khong giao dich vong nay")

        self.stdout.write("  Futures bots xong.")
