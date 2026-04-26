import os
import sys
import threading
import time
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

_bot_loop_started = False
_bot_loop_lock = threading.Lock()


_FUTURES_INTERVAL = 120  # nghỉ 120s giữa các vòng (~94s/round + 120s = ~3.5 phút/chu kỳ)


def _futures_bot_loop():
    time.sleep(30)  # chờ Django + DB ready
    while True:
        try:
            from django.core.management import call_command
            call_command("run_futures_bots")
        except Exception as e:
            logger.error(f"Futures bot loop error: {e}")

        # Sau mỗi round: tự động phân tích lệnh chưa được xem xét
        try:
            from crypto.bots.futures_analyzer import run_auto_analysis
            run_auto_analysis(max_per_run=5)
        except Exception as e:
            logger.error(f"Auto-analyzer error: {e}")

        time.sleep(_FUTURES_INTERVAL)


class CryptoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crypto"

    def ready(self):
        _SKIP = {"migrate", "makemigrations", "shell", "shell_plus",
                 "collectstatic", "test", "check", "create_crypto_bots",
                 "run_crypto_bots", "create_bots", "run_bots",
                 "create_futures_bots", "run_futures_bots"}
        if len(sys.argv) > 1 and sys.argv[1] in _SKIP:
            return
        if os.environ.get("RUN_MAIN") != "true":
            return

        from crypto.services.price_feed import start_crypto_feed
        start_crypto_feed()

        from crypto.services.news_feed import start_news_feed
        start_news_feed()

        global _bot_loop_started
        with _bot_loop_lock:
            if not _bot_loop_started:
                _bot_loop_started = True
                threading.Thread(target=_futures_bot_loop, daemon=True, name="futures_bot_loop").start()
                logger.info(f"Futures bot loop started (interval={_FUTURES_INTERVAL}s). Spot bots disabled.")
