import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Chay crypto bot AI trader mot vong"

    def add_arguments(self, parser):
        parser.add_argument("--bot", type=str, default=None, help="Chi chay 1 bot (username)")

    def handle(self, *args, **options):
        from crypto.bots.definitions import CRYPTO_BOTS
        from crypto.bots.market_context import build_crypto_context, get_crypto_portfolio_state
        from crypto.bots.executor import execute_crypto_decisions
        from crypto.models import CryptoWallet, BotRoundLog
        from bots.ollama_client import ask_llm

        target = options.get("bot")
        bots = [b for b in CRYPTO_BOTS if target is None or b["username"] == target]

        ts = datetime.now().strftime("%H:%M:%S")
        self.stdout.write(f"\n[{ts}] Crypto: chay {len(bots)} bot...")

        for bot_def in bots:
            self.stdout.write(f"  >> {bot_def['display_name']} ({bot_def['model']})")

            try:
                user = User.objects.get(email=bot_def["email"])
                wallet = CryptoWallet.objects.get(user=user)
            except Exception:
                self.stdout.write("  Bot chua duoc tao. Chay: python manage.py create_crypto_bots")
                continue

            portfolio = get_crypto_portfolio_state(user)
            context = build_crypto_context(portfolio, wallet.balance_usd, bot_username=bot_def["username"])

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
            analysis = result.get("analysis", "")
            analysis_ascii = analysis.encode("ascii", errors="replace").decode("ascii")
            self.stdout.write(f"  {len(decisions)} quyet dinh | {analysis_ascii[:80]}")

            # Lưu analysis của vòng này — không tốn thêm LLM call
            BotRoundLog.objects.create(
                bot_username=bot_def["username"],
                analysis_text=analysis,
                decisions_count=len(decisions),
            )

            if decisions:
                logs = execute_crypto_decisions(
                    user, decisions, portfolio,
                    bot_reasoning=analysis[:300],  # tóm tắt reasoning vào mỗi order
                )
                for log in logs:
                    self.stdout.write(log.encode("ascii", errors="replace").decode("ascii"))
            else:
                self.stdout.write("  HOLD - khong giao dich vong nay")

        self.stdout.write("  Crypto bots xong.")
