import time
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

# Futures bots use small context → no need for 16k KV-cache
FUTURES_NUM_CTX     = 4096   # was 16384 → 75% VRAM reduction per inference
FUTURES_NUM_PREDICT = 400    # JSON response ≈ 300 tokens, was 1200 → 3× faster output


class Command(BaseCommand):
    help = "Run one round of futures bot decisions (optimized: small ctx, sorted by model)"

    def add_arguments(self, parser):
        parser.add_argument("--bot", type=str, default=None)

    def handle(self, *args, **options):
        from crypto.bots.futures_definitions import FUTURES_BOTS
        from crypto.bots.futures_context import build_futures_context
        from crypto.bots.futures_executor import get_futures_portfolio_state, execute_futures_decisions
        from crypto.models import FuturesWallet
        from bots.ollama_client import ask_llm

        target = options.get("bot")
        bots = [b for b in FUTURES_BOTS if target is None or b["username"] == target]

        # Sort bots by model name — same models adjacent = Ollama keeps model loaded = 0 swap cost
        # (If all 5 bots have different models this has no effect, but future-proofs the setup)
        bots_sorted = sorted(bots, key=lambda b: b["model"])

        ts = datetime.now().strftime("%H:%M:%S")
        self.stdout.write(f"\n[{ts}] Futures: {len(bots_sorted)} bots | ctx={FUTURES_NUM_CTX} predict={FUTURES_NUM_PREDICT}")

        round_start = time.time()
        prev_model = None

        for bot_def in bots_sorted:
            bot_start = time.time()
            model = bot_def["model"]

            # Log model swap so we can see the overhead
            if prev_model and prev_model != model:
                self.stdout.write(f"  [swap] {prev_model} → {model}")
            prev_model = model

            self.stdout.write(f"  >> {bot_def['display_name']} ({model})")

            try:
                user   = User.objects.get(email=bot_def["email"])
                wallet = FuturesWallet.objects.get(user=user)
            except Exception:
                self.stdout.write("  Bot not found. Run: python manage.py create_futures_bots")
                continue

            positions = get_futures_portfolio_state(user)
            context   = build_futures_context(positions, wallet.balance_usd)

            result = ask_llm(
                model=model,
                system_prompt=bot_def["system_prompt"],
                user_message=context,
                append_json_instruction=False,
                num_ctx=FUTURES_NUM_CTX,
                num_predict=FUTURES_NUM_PREDICT,
                temperature=0.2,     # lower = more deterministic + slightly faster
                keep_alive="15m",    # keep model hot between bots using same model
            )

            elapsed = time.time() - bot_start

            if not result:
                self.stdout.write(f"  No response ({elapsed:.1f}s)")
                continue

            decisions = result.get("decisions", [])
            analysis  = result.get("analysis", "").encode("ascii", errors="replace").decode("ascii")
            self.stdout.write(f"  {len(decisions)} decisions | {analysis[:80]} ({elapsed:.1f}s)")

            if decisions:
                logs = execute_futures_decisions(user, decisions)
                for log in logs:
                    self.stdout.write(log.encode("ascii", errors="replace").decode("ascii"))
            else:
                self.stdout.write("  HOLD this round")

        total = time.time() - round_start
        self.stdout.write(f"  Round done in {total:.1f}s")
