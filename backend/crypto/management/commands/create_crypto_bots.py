from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()
START_CAPITAL_USD = Decimal("5000")


class Command(BaseCommand):
    help = "Tao hoac reset 5 crypto bot AI ($5000 USD/bot)"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Reset ve $5000 va xoa toan bo danh muc + lenh")

    def handle(self, *args, **options):
        from crypto.bots.definitions import CRYPTO_BOTS
        from crypto.models import CryptoWallet, CryptoPortfolio, CryptoOrder

        do_reset = options.get("reset", False)

        for bot in CRYPTO_BOTS:
            user, created = User.objects.get_or_create(
                email=bot["email"],
                defaults={"username": bot["username"], "is_active": True},
            )
            if created:
                user.set_password("bot_crypto_2024!")
                user.save()

            wallet, w_created = CryptoWallet.objects.get_or_create(
                user=user,
                defaults={"balance_usd": START_CAPITAL_USD},
            )

            if do_reset:
                CryptoOrder.objects.filter(user=user).delete()
                CryptoPortfolio.objects.filter(user=user).delete()
                wallet.balance_usd = START_CAPITAL_USD
                wallet.frozen_usd = Decimal("0")
                wallet.save()
                status = "[Reset]"
            elif w_created:
                status = "[Tao moi]"
            else:
                status = "[Da ton tai]"

            self.stdout.write(
                f"{status}: {bot['display_name']} | Model: {bot['model']} | USD: ${wallet.balance_usd:,.2f}"
            )

        self.stdout.write(self.style.SUCCESS("\nXong! Crypto bots san sang."))
        self.stdout.write("Chay bot: python manage.py run_crypto_bots")
