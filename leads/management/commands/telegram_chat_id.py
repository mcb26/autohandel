"""Chat-ID für Telegram-Benachrichtigungen ermitteln."""

import json
from urllib.request import urlopen

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Zeigt Chat-IDs aus den letzten Bot-Nachrichten. "
        "Zuerst dem Bot in Telegram /start schicken, dann diesen Befehl ausführen."
    )

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN ist in der .env nicht gesetzt.")

        url = f"https://api.telegram.org/bot{token}/getUpdates"
        try:
            with urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except OSError as exc:
            raise CommandError(f"Telegram API nicht erreichbar: {exc}") from exc

        if not data.get("ok"):
            raise CommandError(data.get("description", "Unbekannter Telegram-Fehler"))

        updates = data.get("result", [])
        if not updates:
            self.stdout.write(
                self.style.WARNING(
                    "Keine Nachrichten gefunden. Öffnen Sie Ihren Bot in Telegram und senden Sie /start."
                )
            )
            return

        seen = set()
        self.stdout.write(self.style.SUCCESS("Gefundene Chat-IDs (TELEGRAM_NOTIFY_CHAT_ID in .env):"))
        for update in updates:
            message = update.get("message") or update.get("edited_message")
            if not message:
                continue
            chat = message.get("chat", {})
            chat_id = chat.get("id")
            if chat_id is None or chat_id in seen:
                continue
            seen.add(chat_id)
            name = " ".join(
                part
                for part in [
                    chat.get("first_name"),
                    chat.get("last_name"),
                    f"@{chat['username']}" if chat.get("username") else None,
                ]
                if part
            )
            self.stdout.write(f"  {chat_id}  ({name or 'ohne Name'})")
