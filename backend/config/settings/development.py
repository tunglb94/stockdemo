from .base import *

# Dev: bỏ các app cần Redis/PostgreSQL
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in ("django_celery_beat",)]

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

# SQLite cho local dev — không cần PostgreSQL hay Docker
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 30,  # wait up to 30s when locked before raising error
        },
    }
}

# Enable WAL journal mode for SQLite to allow concurrent reads + writes
from django.db.backends.signals import connection_created

def _sqlite_wal(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=30000;")

connection_created.connect(_sqlite_wal)

# Dùng InMemoryChannelLayer khi dev local (không cần Redis)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# Tắt Celery khi dev local (task chạy đồng bộ để test)
CELERY_TASK_ALWAYS_EAGER = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "market_data": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "trading": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}
