"""
Tạo hoặc cập nhật 5 tài khoản bot AI với 100M VNĐ mỗi tài khoản.
Chạy 1 lần: python manage.py create_bots
Chạy lại: an toàn, chỉ cập nhật số dư nếu < 100M (reset vốn).
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()
START_CAPITAL = Decimal("100000000")  # 100 triệu VNĐ


class Command(BaseCommand):
    help = "Tạo hoặc reset 5 tài khoản bot AI trader (100M/bot)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Reset vốn về 100M và xóa toàn bộ danh mục + lệnh của bot"
        )

    def handle(self, *args, **options):
        from bots.definitions import BOTS
        from accounts.models import Wallet

        do_reset = options.get("reset", False)

        for bot in BOTS:
            user, created = User.objects.get_or_create(
                email=bot["email"],
                defaults={
                    "username": bot["username"],
                    "is_active": True,
                },
            )
            if created:
                user.set_password("bot_secure_pass_2024!")
                user.save()

            wallet, w_created = Wallet.objects.get_or_create(
                user=user,
                defaults={"balance": START_CAPITAL},
            )

            if do_reset:
                from trading.models import Order, Portfolio
                Order.objects.filter(user=user).delete()
                Portfolio.objects.filter(user=user).delete()
                wallet.balance = START_CAPITAL
                wallet.frozen_balance = Decimal("0")
                wallet.save(update_fields=["balance", "frozen_balance"])
                status = "[Reset]"
            elif w_created:
                status = "[Tao moi]"
            else:
                if wallet.balance < START_CAPITAL and wallet.frozen_balance == 0:
                    wallet.balance = START_CAPITAL
                    wallet.save(update_fields=["balance"])
                    status = "[Nang von]"
                else:
                    status = "[Da ton tai]"

            self.stdout.write(
                f"{status}: {bot['display_name']} ({bot['email']}) "
                f"| Model: {bot['model']} "
                f"| Von: {wallet.balance:,.0f}d"
            )

        self.stdout.write(self.style.SUCCESS("\nXong! 5 bot da san sang."))
        self.stdout.write("Chay bot ngay: python manage.py run_bots")
