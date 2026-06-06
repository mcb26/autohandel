import re

from django.conf import settings


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _format_phone_display(phone: str) -> str:
    raw = (phone or "").strip()
    digits = _digits(raw)
    if not digits:
        return raw

    if raw.startswith("+"):
        if digits.startswith("49") and len(digits) >= 11:
            local = digits[2:]
            if len(local) == 10:
                return f"+49 {local[:3]} {local[3:6]} {local[6:]}"
            if len(local) == 11:
                return f"+49 {local[:4]} {local[4:7]} {local[7:]}"
        return raw

    if digits.startswith("0") and len(digits) == 11:
        return f"{digits[:4]} {digits[4:7]} {digits[7:]}"

    if digits.startswith("0") and len(digits) == 12:
        return f"{digits[:4]} {digits[4:8]} {digits[8:]}"

    return raw


def _telegram_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith("@"):
        return f"https://t.me/{value[1:]}"
    if value.startswith("http"):
        return value
    digits = _digits(value)
    if digits:
        return f"https://t.me/+{digits}"
    return f"https://t.me/{value.lstrip('@')}"


def _instagram_url(value: str) -> str:
    handle = (value or "").strip().lstrip("@")
    if not handle:
        return ""
    if handle.startswith("http"):
        return handle
    return f"https://www.instagram.com/{handle}/"


def site_brand(request):
    return {
        "site_brand_name": getattr(settings, "SITE_BRAND_NAME", "AutoPark Grün"),
        "site_logo_path": getattr(settings, "SITE_LOGO_PATH", "img/logo.png"),
        "static_asset_version": getattr(settings, "STATIC_ASSET_VERSION", "1"),
    }


def site_contact(request):
    phone = getattr(settings, "SITE_PHONE", "")
    whatsapp = getattr(settings, "SITE_WHATSAPP", "") or phone
    email = getattr(settings, "SITE_EMAIL", "")
    telegram = getattr(settings, "SITE_TELEGRAM", "")
    instagram = getattr(settings, "SITE_INSTAGRAM", "")

    phone_digits = _digits(phone)
    whatsapp_digits = _digits(whatsapp)

    return {
        "site_company_name": getattr(settings, "SITE_COMPANY_NAME", ""),
        "site_address": getattr(settings, "SITE_ADDRESS", ""),
        "site_phone": phone,
        "site_phone_display": _format_phone_display(phone),
        "site_phone_url": f"tel:{phone_digits}" if phone_digits else "",
        "site_email": email,
        "site_email_url": f"mailto:{email}" if email else "",
        "site_whatsapp_url": f"https://wa.me/{whatsapp_digits}" if whatsapp_digits else "",
        "site_telegram_url": _telegram_url(telegram),
        "site_instagram_url": _instagram_url(instagram),
        "site_telegram_label": telegram.lstrip("@") if telegram else "",
        "site_instagram_label": instagram.lstrip("@") if instagram else "",
        "hero_image_attribution": _hero_image_attribution(),
    }


def _hero_image_attribution():
    url = getattr(settings, "HERO_IMAGE_ATTRIBUTION_URL", "").strip()
    if not url:
        return None
    return {
        "title": getattr(settings, "HERO_IMAGE_ATTRIBUTION_TITLE", ""),
        "author": getattr(settings, "HERO_IMAGE_ATTRIBUTION_AUTHOR", ""),
        "source": getattr(settings, "HERO_IMAGE_ATTRIBUTION_SOURCE", "Magnific.com"),
        "url": url,
        "license": getattr(
            settings,
            "HERO_IMAGE_ATTRIBUTION_LICENSE",
            "Kostenlose kommerzielle Nutzung mit Namensnennung (Magnific.com)",
        ),
    }
