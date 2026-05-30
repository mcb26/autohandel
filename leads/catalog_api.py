"""JSON-API für den Fahrzeugkatalog (lazy load pro Marke)."""

from __future__ import annotations

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .catalog_loader import get_brand_catalog, get_brand_list

CACHE_MAX_AGE = 3600


def _json_response(data, *, status: int = 200) -> JsonResponse:
    response = JsonResponse(data, status=status)
    response["Cache-Control"] = f"public, max-age={CACHE_MAX_AGE}"
    return response


@require_GET
def catalog_brands(request):
    brands = get_brand_list()
    return _json_response({"brands": brands})


@require_GET
def catalog_brand_detail(request, brand_slug: str):
    brand = get_brand_catalog(brand_slug)
    if not brand:
        return JsonResponse({"error": "Marke nicht gefunden"}, status=404)
    return _json_response({"key": brand_slug, **brand})
