from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()
START_CAPITAL_USD = Decimal("5000")


class Command(BaseCommand):
    help = "Tao hoac reset 6 futures bot AI (long/short, $5000 USD/bot)"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Reset ve $5000 va xoa toan bo vi tri")

    def handle(self, *args, **options):
        from crypto.bots.futures_definitions import FUTURES_BOTS
        from crypto.models import FuturesWallet, FuturesPosition

        do_reset = options.get("reset", False)

        for bot in FUTURES_BOTS:
            user, created = User.objects.get_or_create(
                email=bot["email"],
                defaults={"username": bot["username"], "is_active": True},
            )
            if created:
                user.set_password("bot_futures_2024!")
                user.save()

            wallet, w_created = FuturesWallet.objects.get_or_create(
                user=user,
                defaults={"balance_usd": START_CAPITAL_USD},
            )

            if do_reset:
                FuturesPosition.objects.filter(user=user).delete()
                wallet.balance_usd = START_CAPITAL_USD
                wallet.used_margin_usd = Decimal("0")
                wallet.save()
                status = "[Reset]"
            elif w_created:
                status = "[Tao moi]"
            else:
                status = "[Da ton tai]"

            self.stdout.write(
                f"{status}: {bot['display_name']} | Model: {bot['model']} | USD: ${wallet.balance_usd:,.2f}"
            )

        self.stdout.write(self.style.SUCCESS("\nXong! Futures bots san sang."))
