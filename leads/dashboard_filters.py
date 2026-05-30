"""Gemeinsame Filter- und KPI-Logik für das Händler-Dashboard."""

from __future__ import annotations

from datetime import timedelta

from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import CarLead

ARCHIVE_VIEW_ACTIVE = "active"
ARCHIVE_VIEW_ARCHIVED = "archived"
ARCHIVE_VIEW_ALL = "all"

DASHBOARD_SORT_FIELDS = {
    "created_at": "created_at",
    "status": "status",
    "customer_name": "customer_name",
    "phone": "phone",
    "email": "email",
    "brand": "brand",
    "model": "model",
    "first_registration": "first_registration",
    "mileage": "mileage",
    "expected_price": "expected_price",
}

DASHBOARD_PAGE_SIZE = 25


def parse_int_param(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def filters_from_request(request) -> dict:
    archive_view = (request.GET.get("view") or ARCHIVE_VIEW_ACTIVE).strip()
    if archive_view not in (ARCHIVE_VIEW_ACTIVE, ARCHIVE_VIEW_ARCHIVED, ARCHIVE_VIEW_ALL):
        archive_view = ARCHIVE_VIEW_ACTIVE

    sort = (request.GET.get("sort") or "created_at").strip()
    if sort not in DASHBOARD_SORT_FIELDS:
        sort = "created_at"
    direction = (request.GET.get("dir") or "desc").strip().lower()
    if direction not in ("asc", "desc"):
        direction = "desc"

    return {
        "q": (request.GET.get("q") or "").strip(),
        "archive_view": archive_view,
        "f_status": (request.GET.get("f_status") or "").strip(),
        "f_brand": (request.GET.get("f_brand") or "").strip(),
        "f_model": (request.GET.get("f_model") or "").strip(),
        "f_created_from": (request.GET.get("f_created_from") or "").strip(),
        "f_created_to": (request.GET.get("f_created_to") or "").strip(),
        "f_reg_from": (request.GET.get("f_reg_from") or "").strip(),
        "f_reg_to": (request.GET.get("f_reg_to") or "").strip(),
        "f_km_min": parse_int_param(request.GET.get("f_km_min")),
        "f_km_max": parse_int_param(request.GET.get("f_km_max")),
        "f_price_min": parse_int_param(request.GET.get("f_price_min")),
        "f_price_max": parse_int_param(request.GET.get("f_price_max")),
        "sort": sort,
        "dir": direction,
        "f_km_min_display": request.GET.get("f_km_min", ""),
        "f_km_max_display": request.GET.get("f_km_max", ""),
        "f_price_min_display": request.GET.get("f_price_min", ""),
        "f_price_max_display": request.GET.get("f_price_max", ""),
    }


def apply_dashboard_filters(queryset: QuerySet[CarLead], filters: dict) -> QuerySet[CarLead]:
    archive_view = filters["archive_view"]
    if archive_view == ARCHIVE_VIEW_ACTIVE:
        queryset = queryset.filter(is_archived=False)
    elif archive_view == ARCHIVE_VIEW_ARCHIVED:
        queryset = queryset.filter(is_archived=True)

    q = filters["q"]
    if q:
        queryset = queryset.filter(
            Q(customer_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(email__icontains=q)
            | Q(brand__icontains=q)
            | Q(model__icontains=q)
            | Q(series__icontains=q)
            | Q(engine__icontains=q)
            | Q(internal_notes__icontains=q)
        )
    if filters["f_status"]:
        queryset = queryset.filter(status=filters["f_status"])
    if filters["f_brand"]:
        queryset = queryset.filter(brand__icontains=filters["f_brand"])
    if filters["f_model"]:
        queryset = queryset.filter(model__icontains=filters["f_model"])
    if filters["f_created_from"]:
        queryset = queryset.filter(created_at__date__gte=filters["f_created_from"])
    if filters["f_created_to"]:
        queryset = queryset.filter(created_at__date__lte=filters["f_created_to"])
    if filters["f_reg_from"]:
        queryset = queryset.filter(first_registration__gte=f"{filters['f_reg_from']}-01")
    if filters["f_reg_to"]:
        queryset = queryset.filter(first_registration__lte=f"{filters['f_reg_to']}-28")
    if filters["f_km_min"] is not None:
        queryset = queryset.filter(mileage__gte=filters["f_km_min"])
    if filters["f_km_max"] is not None:
        queryset = queryset.filter(mileage__lte=filters["f_km_max"])
    if filters["f_price_min"] is not None:
        queryset = queryset.filter(expected_price__gte=filters["f_price_min"])
    if filters["f_price_max"] is not None:
        queryset = queryset.filter(expected_price__lte=filters["f_price_max"])

    order_expr = DASHBOARD_SORT_FIELDS[filters["sort"]]
    if filters["dir"] == "desc":
        order_expr = f"-{order_expr}"
    return queryset.order_by(order_expr, "-pk")


def build_dashboard_queryset(request) -> QuerySet[CarLead]:
    filters = filters_from_request(request)
    return apply_dashboard_filters(CarLead.objects.all(), filters)


def dashboard_kpis() -> dict[str, int]:
    """Kennzahlen für aktive (nicht archivierte) Anfragen."""
    base = CarLead.objects.filter(is_archived=False)
    now = timezone.localtime()
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return {
        "new_count": base.filter(status=CarLead.STATUS_NEW).count(),
        "open_count": base.filter(
            status__in=[CarLead.STATUS_NEW, CarLead.STATUS_CONTACTED]
        ).count(),
        "week_count": base.filter(created_at__gte=week_start).count(),
    }


def adjacent_lead_pks(request, current_pk: int) -> tuple[int | None, int | None]:
    pks = list(build_dashboard_queryset(request).values_list("pk", flat=True))
    try:
        index = pks.index(current_pk)
    except ValueError:
        return None, None
    prev_pk = pks[index - 1] if index > 0 else None
    next_pk = pks[index + 1] if index < len(pks) - 1 else None
    return prev_pk, next_pk


def list_query_string(request) -> str:
    query = request.GET.urlencode()
    return f"?{query}" if query else ""
