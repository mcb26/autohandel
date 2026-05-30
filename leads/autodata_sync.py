"""Lädt Marken, Modelle, Baureihen und Motorisierungen von auto-data.net in den Cache."""

from __future__ import annotations

import argparse
import time

from .autodata_client import CACHE_DIR, get_all_brands, get_generations, get_models, get_trims
from .catalog_builder import POPULAR_BRANDS


def _brand_matches(brand: dict, wanted: set[str]) -> bool:
    label = brand["label"].upper()
    slug = brand["slug"].upper()
    for name in wanted:
        n = name.upper()
        if n == label or n == slug or n.replace(" ", "-") == slug:
            return True
        if n == "VW" and label in ("VW", "VOLKSWAGEN"):
            return True
        if n == "MERCEDES-BENZ" and "MERCEDES" in label:
            return True
        if n == "MG" and label == "MG":
            return True
        if n in ("SSANGYONG", "SSANG YONG") and "SSANG" in label:
            return True
        if n == "NIO" and label == "NIO":
            return True
        if n == "BYD" and label == "BYD":
            return True
    return False


def sync(
    brand_filter: list[str] | None = None,
    *,
    fetch_trims: bool = True,
) -> dict[str, int]:
    stats = {
        "brands": 0,
        "models": 0,
        "generations": 0,
        "trims": 0,
        "errors": 0,
    }

    brands = get_all_brands(fetch=True)
    if brand_filter:
        wanted = {b.strip() for b in brand_filter if b.strip()}
        brands = [b for b in brands if _brand_matches(b, wanted)]

    for brand in brands:
        stats["brands"] += 1
        print(
            f"\n=== {brand['label']} ({stats['brands']}/{len(brands)}) ===",
            flush=True,
        )
        models = get_models(brand, fetch=True)
        stats["models"] += len(models)

        for model_idx, model in enumerate(models, start=1):
            print(f"  [{model_idx}/{len(models)}] {model['label']} …", end="", flush=True)
            generations = get_generations(model, brand, fetch=True)
            stats["generations"] += len(generations)
            trim_count = 0
            if fetch_trims:
                for generation in generations:
                    trims = get_trims(generation, fetch=True)
                    trim_count += len(trims)
                stats["trims"] += trim_count
            print(
                f" {len(generations)} Baureihen"
                + (f", {trim_count} Motorisierungen" if fetch_trims else ""),
                flush=True,
            )

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="auto-data.net in den Cache laden.")
    parser.add_argument(
        "--brands",
        help="Kommagetrennte Marken (z. B. VW,BMW,Mercedes-Benz)",
    )
    parser.add_argument(
        "--popular-only",
        action="store_true",
        help=f"Nur: {', '.join(POPULAR_BRANDS)}",
    )
    parser.add_argument(
        "--generations-only",
        action="store_true",
        help="Keine Motorisierungen laden (schneller)",
    )
    args = parser.parse_args()

    if args.popular_only:
        brand_filter = POPULAR_BRANDS
    elif args.brands:
        brand_filter = [b.strip() for b in args.brands.split(",") if b.strip()]
    else:
        brand_filter = None

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()
    stats = sync(brand_filter, fetch_trims=not args.generations_only)
    elapsed = time.time() - started
    print(
        f"\nFertig in {elapsed:.0f}s – Marken: {stats['brands']}, "
        f"Modelle: {stats['models']}, Baureihen: {stats['generations']}, "
        f"Motorisierungen: {stats['trims']}",
        flush=True,
    )
    print(f"Cache: {CACHE_DIR}", flush=True)


if __name__ == "__main__":
    main()
