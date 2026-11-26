from django.conf import settings
from django.core.management.base import BaseCommand

from apps.accounts.telegram_bot import run_polling


class Command(BaseCommand):
    help = "Run the Telegram bot by polling. For local development only."

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stdout.write(
                "TELEGRAM_BOT_TOKEN is empty, so the bot was not started. "
                "Set it in .env to log in through Telegram locally."
            )
            return
        self.stdout.write("The Telegram bot is polling. Press Ctrl+C to stop.")
        try:
            run_polling()
        except KeyboardInterrupt:
            self.stdout.write("The Telegram bot stopped.")
