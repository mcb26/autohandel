"""Baut vehicle_catalog.json aus dem auto-data.net-Cache."""

from __future__ import annotations

import json
from pathlib import Path

from .autodata_client import (
    BRAND_LABEL_OVERRIDES,
    CACHE_DIR,
    GENERIC_ENGINES,
    get_all_brands,
    get_engines_for_generation,
    get_generations,
    get_models,
    slugify,
)


def _display_brand_label(brand: dict) -> str:
    slug = brand.get("slug", "")
    if slug in BRAND_LABEL_OVERRIDES:
        return BRAND_LABEL_OVERRIDES[slug]
    return brand["label"]

DATA_DIR = Path(__file__).resolve().parent / "data"
OUTPUT_PATH = DATA_DIR / "vehicle_catalog.json"
CATALOG_BRANDS_INDEX = DATA_DIR / "catalog" / "brands.json"
CATALOG_BRANDS_DIR = DATA_DIR / "catalog" / "brands"

POPULAR_BRANDS = [
    "VW",
    "Mercedes-Benz",
    "BMW",
    "Audi",
    "Opel",
    "Ford",
    "Skoda",
    "Renault",
    "SEAT",
    "Toyota",
    "Hyundai",
    "Kia",
    "Peugeot",
    "Fiat",
    "Tesla",
    # Weitere häufige Marken in Deutschland
    "Cupra",
    "Dacia",
    "Volvo",
    "Mazda",
    "Honda",
    "Nissan",
    "Citroën",
    "Mini",
    "Porsche",
    "DS",
    # +20 weitere Marken
    "Suzuki",
    "Mitsubishi",
    "Subaru",
    "Jeep",
    "Land Rover",
    "Jaguar",
    "Alfa Romeo",
    "Smart",
    "MG",
    "Polestar",
    "Lexus",
    "Lancia",
    "Genesis",
    "SsangYong",
    "Infiniti",
    "Chevrolet",
    "Chrysler",
    "Cadillac",
    "Dodge",
    "Abarth",
    # +5 weitere Marken
    "BYD",
    "NIO",
    "Saab",
    "Aston Martin",
    "Maserati",
]


def _brands_with_cached_models() -> list[dict]:
    """Nur Marken, die per autodata_sync bereits importiert wurden."""
    models_dir = CACHE_DIR / "models"
    if not models_dir.is_dir():
        return []
    synced_slugs = {p.stem for p in models_dir.glob("*.json")}
    brands = get_all_brands(fetch=False) or get_all_brands(fetch=True)
    return [b for b in brands if b.get("slug") in synced_slugs]


def build_catalog() -> dict:
    catalog: dict = {}
    brands = _brands_with_cached_models()
    if not brands:
        return catalog

    popular_keys = {b.upper() for b in POPULAR_BRANDS}
    popular: list[dict] = []
    other: list[dict] = []
    for brand in brands:
        if _display_brand_label(brand).upper() in popular_keys:
            popular.append(brand)
        else:
            other.append(brand)
    other.sort(key=lambda b: b["label"].lower())
    ordered = popular + other

    for brand in ordered:
        models_map: dict = {}
        for model in get_models(brand, fetch=False):
            generations = get_generations(model, brand, fetch=False)
            if not generations:
                generations = [
                    {
                        "id": "default",
                        "slug": slugify(model["label"]),
                        "label": model["label"],
                    }
                ]

            series_dict: dict = {}
            for gen in generations:
                key = gen.get("slug") or slugify(gen["label"]) or f"gen-{gen.get('id')}"
                engines = get_engines_for_generation(gen, fetch=False)
                series_dict[key] = {
                    "label": gen["label"],
                    "engines": engines,
                }

            model_key = model.get("slug") or slugify(model["label"])
            models_map[model_key] = {
                "label": model["label"],
                "series": series_dict,
            }

        if models_map:
            catalog[brand["slug"]] = {
                "label": _display_brand_label(brand),
                "models": models_map,
            }

    return catalog


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not _brands_with_cached_models():
        print(
            "Hinweis: Kein auto-data.net-Import. Zuerst:\n"
            "  python3 -m leads.autodata_sync --popular-only\n"
            "  python3 -m leads.catalog_builder"
        )

    catalog = build_catalog()
    OUTPUT_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    CATALOG_BRANDS_DIR.mkdir(parents=True, exist_ok=True)
    brands_index = [{"key": key, "label": data["label"]} for key, data in catalog.items()]
    CATALOG_BRANDS_INDEX.write_text(
        json.dumps(brands_index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for key, data in catalog.items():
        (CATALOG_BRANDS_DIR / f"{key}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    model_count = sum(len(b["models"]) for b in catalog.values())
    series_count = sum(
        len(m["series"]) for b in catalog.values() for m in b["models"].values()
    )
    with_trims = sum(
        1
        for b in catalog.values()
        for m in b["models"].values()
        for s in m["series"].values()
        if s["engines"] != GENERIC_ENGINES
    )
    print(
        f"Written {OUTPUT_PATH}: {len(catalog)} brands, {model_count} models, "
        f"{series_count} series ({with_trims} mit Motorisierungen)"
    )
    print(f"Split catalog: {CATALOG_BRANDS_INDEX} + {len(catalog)} files in {CATALOG_BRANDS_DIR}")


if __name__ == "__main__":
    main()
