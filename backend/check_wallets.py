import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()
from django.contrib.auth import get_user_model
from accounts.models import Wallet
from bots.definitions import BOTS
from trading.models import Portfolio

User = get_user_model()
START = 100_000_000

print(f"{'Bot':<28} {'Cash':>14} {'Frozen':>12} {'Cash+Frozen':>14} {'vs 100M':>10}")
print('-'*80)
for b in BOTS:
    try:
        u = User.objects.get(email=b['email'])
        w = Wallet.objects.get(user=u)
        total_cash = w.balance + w.frozen_balance
        diff = float(total_cash) - START
        sign = "+" if diff >= 0 else ""
        print(f"{b['display_name']:<28} {float(w.balance):>14,.0f} {float(w.frozen_balance):>12,.0f} {float(total_cash):>14,.0f} {sign}{diff/1000:>8.0f}K")
    except Exception as e:
        print(f"{b['display_name']:<28} ERROR: {e}")
