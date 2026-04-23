from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CryptoAsset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("symbol", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("category", models.CharField(choices=[("CRYPTO", "Cryptocurrency"), ("COMMODITY", "Commodity")], default="CRYPTO", max_length=20)),
                ("coingecko_id", models.CharField(blank=True, max_length=100)),
                ("yfinance_ticker", models.CharField(blank=True, max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("rank", models.IntegerField(default=999)),
            ],
            options={"ordering": ["rank"]},
        ),
        migrations.CreateModel(
            name="CryptoSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("price_usd", models.DecimalField(decimal_places=8, max_digits=20)),
                ("change_24h", models.FloatField(default=0)),
                ("volume_24h", models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ("market_cap", models.DecimalField(decimal_places=2, default=0, max_digits=20)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="snapshots", to="crypto.cryptoasset")),
            ],
            options={"ordering": ["-timestamp"], "get_latest_by": "timestamp"},
        ),
        migrations.CreateModel(
            name="CryptoWallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("balance_usd", models.DecimalField(decimal_places=4, default=0, max_digits=20)),
                ("frozen_usd", models.DecimalField(decimal_places=4, default=0, max_digits=20)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="crypto_wallet", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="CryptoPortfolio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("quantity", models.DecimalField(decimal_places=8, max_digits=20)),
                ("avg_cost_usd", models.DecimalField(decimal_places=8, max_digits=20)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crypto_portfolio", to=settings.AUTH_USER_MODEL)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="crypto.cryptoasset")),
            ],
            options={"unique_together": {("user", "asset")}},
        ),
        migrations.CreateModel(
            name="CryptoOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("side", models.CharField(choices=[("BUY", "Buy"), ("SELL", "Sell")], max_length=4)),
                ("quantity", models.DecimalField(decimal_places=8, max_digits=20)),
                ("price_usd", models.DecimalField(decimal_places=8, max_digits=20)),
                ("total_usd", models.DecimalField(decimal_places=4, max_digits=20)),
                ("status", models.CharField(choices=[("MATCHED", "Matched"), ("CANCELLED", "Cancelled")], default="MATCHED", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="crypto_orders", to=settings.AUTH_USER_MODEL)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="crypto.cryptoasset")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
