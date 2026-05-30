import re

from django.conf import settings


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


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
