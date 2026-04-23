from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("crypto", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FuturesWallet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("balance_usd", models.DecimalField(decimal_places=4, default=0, max_digits=20)),
                ("used_margin_usd", models.DecimalField(decimal_places=4, default=0, max_digits=20)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="futures_wallet", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="FuturesPosition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("direction", models.CharField(choices=[("LONG", "Long"), ("SHORT", "Short")], max_length=5)),
                ("quantity", models.DecimalField(decimal_places=8, max_digits=20)),
                ("entry_price", models.DecimalField(decimal_places=8, max_digits=20)),
                ("exit_price", models.DecimalField(decimal_places=8, max_digits=20, null=True, blank=True)),
                ("margin_usd", models.DecimalField(decimal_places=4, max_digits=20)),
                ("leverage", models.IntegerField(default=1)),
                ("status", models.CharField(choices=[("OPEN", "Open"), ("CLOSED", "Closed"), ("LIQUIDATED", "Liquidated")], default="OPEN", max_length=12)),
                ("realized_pnl", models.DecimalField(decimal_places=4, max_digits=20, null=True, blank=True)),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                ("closed_at", models.DateTimeField(null=True, blank=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="futures_positions", to=settings.AUTH_USER_MODEL)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="crypto.cryptoasset")),
            ],
            options={"ordering": ["-opened_at"]},
        ),
    ]
