"""Lädt den Fahrzeugkatalog (aufgeteilt pro Marke für schnelle API-Auslieferung)."""

from __future__ import annotations

import json
from pathlib import Path

from .catalog_builder import POPULAR_BRANDS

DATA_DIR = Path(__file__).resolve().parent / "data"
_CATALOG_PATH = DATA_DIR / "vehicle_catalog.json"
_CATALOG_BRANDS_INDEX = DATA_DIR / "catalog" / "brands.json"
_CATALOG_BRANDS_DIR = DATA_DIR / "catalog" / "brands"

_catalog_cache: dict | None = None
_catalog_mtime: float | None = None
_brands_index_cache: list[dict] | None = None
_brands_index_mtime: float | None = None
_brand_cache: dict[str, dict] = {}
_brand_cache_mtime: dict[str, float] = {}


def load_vehicle_catalog() -> dict:
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def get_vehicle_catalog() -> dict:
    """Vollständiger Katalog (Legacy / Validierung)."""
    global _catalog_cache, _catalog_mtime
    if not _CATALOG_PATH.is_file():
        return {}
    mtime = _CATALOG_PATH.stat().st_mtime
    if _catalog_cache is None or _catalog_mtime != mtime:
        _catalog_cache = load_vehicle_catalog()
        _catalog_mtime = mtime
        _brand_cache.clear()
        _brand_cache_mtime.clear()
    return _catalog_cache


def get_brand_list() -> list[dict]:
    """Leichte Markenliste [{key, label}, …] ohne vollen Katalog."""
    global _brands_index_cache, _brands_index_mtime
    if _CATALOG_BRANDS_INDEX.is_file():
        mtime = _CATALOG_BRANDS_INDEX.stat().st_mtime
        if _brands_index_cache is None or _brands_index_mtime != mtime:
            data = json.loads(_CATALOG_BRANDS_INDEX.read_text(encoding="utf-8"))
            _brands_index_cache = data if isinstance(data, list) else []
            _brands_index_mtime = mtime
        return _brands_index_cache

    catalog = get_vehicle_catalog()
    return [{"key": key, "label": value["label"]} for key, value in catalog.items()]


def get_brand_catalog(brand_key: str) -> dict | None:
    """Ein Markenbaum inkl. Modelle, Baureihen und Motorisierungen."""
    if not brand_key:
        return None

    brand_file = _CATALOG_BRANDS_DIR / f"{brand_key}.json"
    if brand_file.is_file():
        mtime = brand_file.stat().st_mtime
        if brand_key not in _brand_cache or _brand_cache_mtime.get(brand_key) != mtime:
            _brand_cache[brand_key] = json.loads(brand_file.read_text(encoding="utf-8"))
            _brand_cache_mtime[brand_key] = mtime
        return _brand_cache[brand_key]

    catalog = get_vehicle_catalog()
    return catalog.get(brand_key)


def ordered_brand_choices() -> list[tuple[str, str]]:
    brands = get_brand_list()
    popular_keys = set(POPULAR_BRANDS)
    popular: list[tuple[str, str]] = []
    other: list[tuple[str, str]] = []
    for item in brands:
        pair = (item["key"], item["label"])
        if item["label"] in popular_keys:
            popular.append(pair)
        else:
            other.append(pair)
    popular.sort(key=lambda x: POPULAR_BRANDS.index(x[1]) if x[1] in POPULAR_BRANDS else 999)
    other.sort(key=lambda x: x[1].lower())
    return popular + other
