import django, os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model
from crypto.bots.definitions import CRYPTO_BOTS
from crypto.models import CryptoWallet, CryptoOrder, CryptoPortfolio

User = get_user_model()
START_CAPITAL_USD = Decimal("100000.0000")

for b in CRYPTO_BOTS:
    try:
        user = User.objects.get(email=b["email"])
        deleted_orders = CryptoOrder.objects.filter(user=user).delete()[0]
        deleted_portfolio = CryptoPortfolio.objects.filter(user=user).delete()[0]
        wallet, _ = CryptoWallet.objects.get_or_create(user=user)
        wallet.balance_usd = START_CAPITAL_USD
        wallet.frozen_usd = Decimal("0")
        wallet.save(update_fields=["balance_usd", "frozen_usd"])
        sys.stdout.buffer.write(
            f"[OK] {b['display_name']}: xoa {deleted_orders} lenh, {deleted_portfolio} portfolio, reset ve $100,000\n".encode("utf-8")
        )
    except Exception as e:
        sys.stdout.buffer.write(f"[Error] {b['display_name']}: {e}\n".encode("utf-8"))

sys.stdout.buffer.write(b"\nDone! Tat ca crypto bot da reset ve $100,000 USD.\n")
