"""Hubraum/Leistung aus Motorisierungs-Labels und Katalog-Einträgen."""

from __future__ import annotations

import re

FUEL_LABELS = {
    "benzin": "Benzin",
    "diesel": "Diesel",
    "elektro": "Elektro",
    "hybrid": "Hybrid",
    "gas": "Gas (LPG/CNG)",
    "other": "Sonstiges",
}


def parse_displacement_liters(label: str) -> str:
    """Hubraum in Litern aus Motorisierungs-Bezeichnung (z. B. 2.0 TDI → 2.0)."""
    if not label:
        return ""
    match = re.search(
        r"(?:^|[\s(])(\d+(?:\.\d+)?)\s*(?:l|L|Liter)?(?:\s|\(|$|TDI|TSI|CDI|d|i|V\d)",
        label,
        re.IGNORECASE,
    )
    if match:
        return match.group(1)
    match = re.search(r"(\d+\.\d+)\s*(?:TSI|TDI|CDI|HDI|DCI|d|i)", label, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def enrich_engine_entry(entry: dict) -> dict:
    """Ergänzt fehlende Hubraum-/Kraftstoff-Felder aus dem Label."""
    result = dict(entry)
    if not result.get("displacement"):
        displacement = parse_displacement_liters(result.get("label", ""))
        if displacement:
            result["displacement"] = displacement
    return result


def find_engine_in_catalog(
    brand_data: dict | None,
    model_key: str,
    series_key: str,
    engine_label: str,
) -> dict:
    if not brand_data or not engine_label:
        return {}
    models = brand_data.get("models", {})
    model = models.get(model_key)
    if not model:
        return {}
    series = model.get("series", {}).get(series_key)
    if not series:
        return {}
    for engine in series.get("engines", []):
        if engine.get("label") == engine_label:
            return enrich_engine_entry(engine)
    return {}
