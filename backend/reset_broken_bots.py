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
BROKEN = {"bot_eta", "bot_theta"}

for b in BOTS:
    if b["username"] not in BROKEN:
        continue
    try:
        user = User.objects.get(email=b["email"])
        wallet = Wallet.objects.get(user=user)
        Order.objects.filter(user=user).delete()
        Portfolio.objects.filter(user=user).delete()
        wallet.balance = START_CAPITAL
        wallet.frozen_balance = Decimal("0")
        wallet.save(update_fields=["balance", "frozen_balance"])
        sys.stdout.buffer.write(f"[Reset] {b['display_name']} OK\n".encode("utf-8"))
    except Exception as e:
        sys.stdout.buffer.write(f"[Error] {b['display_name']}: {e}\n".encode("utf-8"))

sys.stdout.buffer.write(b"Done!\n")
