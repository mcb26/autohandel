import re

from django import template
from django.utils.http import urlencode


register = template.Library()


@register.filter
def telegram_phone_url(phone: str) -> str:
    """Telegram-Chat zu einer Telefonnummer (t.me/+…)."""
    digits = re.sub(r"\D", "", phone or "")
    return f"https://t.me/+{digits}" if digits else ""


@register.filter
def dashboard_status_badge(status: str) -> str:
    mapping = {
        "new": "text-bg-success",
        "contacted": "text-bg-primary",
        "rejected": "text-bg-secondary",
        "bought": "badge-bought",
    }
    return mapping.get(status, "text-bg-dark")


@register.simple_tag(takes_context=True)
def dashboard_query(context, **updates):
    """Baut Query-String aus aktuellen GET-Parametern mit optionalen Änderungen."""
    request = context.get("request")
    if not request:
        return ""
    params = request.GET.copy()
    for key, value in updates.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = str(value)
    encoded = urlencode(params, doseq=True)
    return f"?{encoded}" if encoded else "?"


@register.simple_tag(takes_context=True)
def dashboard_sort_href(context, field: str) -> str:
    """URL zum Sortieren einer Spalte (Richtung wird umgeschaltet)."""
    request = context.get("request")
    if not request:
        return "?"
    current_sort = context.get("sort", "created_at")
    current_dir = context.get("dir", "desc")
    if current_sort == field:
        next_dir = "desc" if current_dir == "asc" else "asc"
    elif field in ("created_at", "mileage", "expected_price", "first_registration"):
        next_dir = "desc"
    else:
        next_dir = "asc"
    params = request.GET.copy()
    params["sort"] = field
    params["dir"] = next_dir
    params.pop("page", None)
    encoded = urlencode(params, doseq=True)
    return f"?{encoded}" if encoded else "?"


@register.simple_tag
def dashboard_sort_indicator(current_sort: str, current_dir: str, field: str) -> str:
    if current_sort != field:
        return "↕"
    return "↑" if current_dir == "asc" else "↓"
