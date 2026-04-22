import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("stocksim")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Fetch market data every 5 minutes during trading hours
    "fetch-market-data": {
        "task": "market_data.tasks.fetch_and_update_market_data",
        "schedule": crontab(minute="*/5", hour="9-15", day_of_week="1-5"),
    },
    # Settle T+2 orders every morning at 9:00
    "settle-t-plus": {
        "task": "trading.tasks.process_t_plus_settlement",
        "schedule": crontab(hour=9, minute=0, day_of_week="1-5"),
    },
    # Update leaderboard every 30 minutes
    "update-leaderboard": {
        "task": "trading.tasks.update_leaderboard",
        "schedule": crontab(minute="*/30", hour="9-16", day_of_week="1-5"),
    },
}
