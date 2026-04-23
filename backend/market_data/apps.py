import sys
from django.apps import AppConfig


class MarketDataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "market_data"
    verbose_name = "Dữ liệu thị trường"

    def ready(self):
        # Không chạy khi migrate/makemigrations/shell/test/...
        _SKIP = {"migrate", "makemigrations", "shell", "shell_plus",
                 "collectstatic", "test", "check"}
        if len(sys.argv) > 1 and sys.argv[1] in _SKIP:
            return

        # Django autoreloader khởi động process 2 lần — chỉ chạy ở lần thứ 2
        import os
        if os.environ.get("RUN_MAIN") != "true":
            return

        from market_data.services.market_feed import start
        start()
