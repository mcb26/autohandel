"""Telegram-Benachrichtigungen für neue Leads (Bot API)."""

from __future__ import annotations

import html
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.urls import reverse

from .models import CarLead

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def telegram_is_configured() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_NOTIFY_CHAT_IDS)


def lead_dashboard_url(lead: CarLead) -> str:
    path = reverse("leads:dashboard_lead_detail", args=[lead.pk])
    base = (settings.SITE_BASE_URL or "").rstrip("/")
    if not base:
        return path
    return f"{base}{path}"


def build_lead_notification_text(lead: CarLead) -> str:
    mileage = f"{lead.mileage:,}".replace(",", ".")
    condition = lead.get_vehicle_condition_display()
    price = f"{lead.expected_price} EUR" if lead.expected_price is not None else "–"
    dashboard_url = lead_dashboard_url(lead)

    lines = [
        "🚗 <b>Neues Angebot</b>",
        "",
        f"<b>Kunde:</b> {html.escape(lead.customer_name)}",
        f"<b>Fahrzeug:</b> {html.escape(lead.vehicle_summary())}",
    ]
    if lead.engine_technical_summary:
        lines.append(f"<b>Technik:</b> {html.escape(lead.engine_technical_summary)}")
    lines.extend(
        [
            f"<b>Erstzulassung:</b> {html.escape(lead.first_registration_display)}",
            f"<b>TÜV bis:</b> {html.escape(lead.tuv_until_display)}",
            f"<b>Kraftstoff:</b> {html.escape(lead.get_fuel_type_display() if lead.fuel_type else '–')}",
            f"<b>Farbe:</b> {html.escape(lead.get_vehicle_color_display() if lead.vehicle_color else '–')}",
            f"<b>Kilometerstand:</b> {html.escape(mileage)} km",
            f"<b>Zustand:</b> {html.escape(condition)}",
            f"<b>Angemeldet:</b> {html.escape(lead.get_is_registered_display() if lead.is_registered else '–')}",
            f"<b>Preisvorstellung:</b> {html.escape(price)}",
            f"<b>Telefon:</b> {html.escape(lead.phone)}",
            f"<b>E-Mail:</b> {html.escape(lead.email)}",
            f"<b>PLZ:</b> {html.escape(lead.postal_code)}",
        ]
    )
    features = lead.active_vehicle_features()
    if features:
        lines.append(f"<b>Merkmale:</b> {html.escape(', '.join(features))}")
    extras = lead.selected_vehicle_extras()
    if extras:
        lines.append(f"<b>Extras:</b> {html.escape(', '.join(extras))}")
    if lead.message:
        lines.append(f"<b>Nachricht:</b> {html.escape(lead.message[:500])}")
    lines.extend(
        [
            "",
            f'<a href="{html.escape(dashboard_url)}">Im Dashboard öffnen</a>',
        ]
    )
    return "\n".join(lines)


def _api_request(token: str, method: str, payload: dict) -> dict:
    url = TELEGRAM_API.format(token=token, method=method)
    body = urlencode(payload).encode("utf-8")
    request = Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def send_telegram_message(text: str, *, chat_id: str | int) -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return False
    try:
        result = _api_request(
            token,
            "sendMessage",
            {
                "chat_id": str(chat_id),
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": "false",
            },
        )
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.warning("Telegram sendMessage fehlgeschlagen (chat_id=%s): %s", chat_id, exc)
        return False

    if not result.get("ok"):
        logger.warning(
            "Telegram API Fehler (chat_id=%s): %s",
            chat_id,
            result.get("description", result),
        )
        return False
    return True


def send_lead_telegram_notification(lead: CarLead) -> None:
    if not telegram_is_configured():
        return

    text = build_lead_notification_text(lead)
    for chat_id in settings.TELEGRAM_NOTIFY_CHAT_IDS:
        send_telegram_message(text, chat_id=chat_id)
