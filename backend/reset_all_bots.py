import django, os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model
from accounts.models import Wallet
from trading.models import Order, Portfolio
from bots.definitions import BOTS

User = get_user_model()
START_CAPITAL = Decimal("100000000")

for b in BOTS:
    try:
        user = User.objects.get(email=b["email"])
        wallet = Wallet.objects.get(user=user)
        deleted_orders = Order.objects.filter(user=user).delete()[0]
        deleted_portfolio = Portfolio.objects.filter(user=user).delete()[0]
        wallet.balance = START_CAPITAL
        wallet.frozen_balance = Decimal("0")
        wallet.save(update_fields=["balance", "frozen_balance"])
        sys.stdout.buffer.write(
            f"[OK] {b['display_name']}: xoa {deleted_orders} lenh, {deleted_portfolio} portfolio, reset ve 100M\n".encode("utf-8")
        )
    except Exception as e:
        sys.stdout.buffer.write(f"[Error] {b['display_name']}: {e}\n".encode("utf-8"))

sys.stdout.buffer.write(b"\nDone! Tat ca bot da reset ve 100,000,000 VND.\n")
