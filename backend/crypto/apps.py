import os
import sys
import threading
import time
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

_bot_loop_started = False
_bot_loop_lock = threading.Lock()


_CRYPTO_SPOT_ENABLED = False  # Tam dung spot bots, nhuong VRAM cho futures
_CRYPTO_INTERVAL = 100   # 3x faster than original 5min (was 300s)
_FUTURES_INTERVAL = 100


def _crypto_bot_loop():
    if not _CRYPTO_SPOT_ENABLED:
        logger.info("Crypto spot bots disabled (_CRYPTO_SPOT_ENABLED=False).")
        return
    time.sleep(30)
    while True:
        try:
            from django.core.management import call_command
            call_command("run_crypto_bots")
        except Exception as e:
            logger.error(f"Crypto bot loop error: {e}")
        time.sleep(_CRYPTO_INTERVAL)


def _futures_bot_loop():
    time.sleep(60)  # stagger after crypto bots
    while True:
        try:
            from django.core.management import call_command
            call_command("run_futures_bots")
        except Exception as e:
            logger.error(f"Futures bot loop error: {e}")
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
                threading.Thread(target=_crypto_bot_loop, daemon=True, name="crypto_bot_loop").start()
                threading.Thread(target=_futures_bot_loop, daemon=True, name="futures_bot_loop").start()
                logger.info(f"Crypto + Futures bot loops started (interval={_CRYPTO_INTERVAL}s).")
