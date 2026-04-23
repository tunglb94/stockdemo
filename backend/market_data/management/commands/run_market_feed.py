"""
Management command: chạy vòng lặp fetch giá và broadcast WebSocket.
Dùng cho dev local (không cần Celery/Redis).
  python manage.py run_market_feed
  python manage.py run_market_feed --interval 30 --symbols VN30
  python manage.py run_market_feed --interval 60 --symbols ALL
"""
import time
import signal
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)
_running = True


def _stop(sig, frame):
    global _running
    _running = False


class Command(BaseCommand):
    help = "Chạy feed giá realtime (vòng lặp fetch + broadcast WebSocket)"

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=int, default=30,
                            help="Giây giữa mỗi lần fetch (default: 30)")
        parser.add_argument("--symbols", default="VN30",
                            help="VN30 hoặc ALL (default: VN30)")

    def handle(self, *args, **options):
        interval = options["interval"]
        mode = options["symbols"].upper()

        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)

        self.stdout.write(self.style.SUCCESS(
            f"Market feed started — mode={mode}, interval={interval}s. Ctrl+C để dừng."
        ))

        from market_data.services.data_processor import (
            ensure_vn30_stocks_exist, save_price_snapshot
        )
        from market_data.services.vnstock_client import (
            fetch_all_vn30_prices, fetch_all_prices
        )

        ensure_vn30_stocks_exist()

        while _running:
            t0 = time.time()
            try:
                if mode == "ALL":
                    prices = fetch_all_prices()
                else:
                    prices = fetch_all_vn30_prices()

                ok = sum(1 for p in prices if save_price_snapshot(p))
                self.stdout.write(f"[feed] Cập nhật {ok}/{len(prices)} mã.")
            except Exception as e:
                logger.error(f"[feed] Lỗi: {e}")

            elapsed = time.time() - t0
            sleep_for = max(0, interval - elapsed)
            if _running and sleep_for:
                time.sleep(sleep_for)

        self.stdout.write(self.style.WARNING("Market feed stopped."))
