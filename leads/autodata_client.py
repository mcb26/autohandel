"""auto-data.net Fahrzeugkatalog per HTTP (Marken → Modelle → Generationen → Motorisierungen)."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from html import unescape
from pathlib import Path

BASE_URL = "https://www.auto-data.net"
LOCALE = "en"
CACHE_DIR = Path(__file__).resolve().parent / "data" / "autodata" / "cache"
USER_AGENT = "AutoParkGrün-Catalog/1.0 (+local build; auto-data.net)"
FETCH_DELAY_SEC = 0.12

GENERIC_ENGINES = [
    {
        "label": "Keine exakte Motorliste verfügbar – bitte genaue Motorisierung im Freitext angeben"
    },
    {"label": "Sonstige Motorisierung (bitte in Nachricht ergänzen)"},
]

BRAND_LINK_RE = re.compile(
    r'href="(/'
    + LOCALE
    + r'/[a-z0-9-]+-brand-(\d+))"[^>]*title="([^"]+)"',
    re.IGNORECASE,
)
MODEL_LINK_RE = re.compile(
    r'href="(/'
    + LOCALE
    + r'/[a-z0-9-]+-model-(\d+))"[^>]*title="([^"]+)"',
    re.IGNORECASE,
)
GENERATION_LINK_RE = re.compile(
    r'href="(/'
    + LOCALE
    + r'/[a-z0-9-]+-generation-(\d+))"[^>]*title="([^"]+)"',
    re.IGNORECASE,
)
TRIM_RE = re.compile(
    r'<span class="tit">([^<]+)</span>\s*(?:<span class="end">([^<]*)</span>)?',
    re.IGNORECASE,
)

BRAND_LABEL_OVERRIDES = {
    "volkswagen": "VW",
    "mercedes-benz": "Mercedes-Benz",
    "bmw": "BMW",
    "skoda": "Skoda",
    "seat": "SEAT",
    "citroen": "Citroën",
    "ds": "DS",
    "mini": "Mini",
    "alfa-romeo": "Alfa Romeo",
    "land-rover": "Land Rover",
    "rolls-royce": "Rolls-Royce",
    "great-wall": "Great Wall",
    "mg": "MG",
    "ssangyong": "SsangYong",
    "nio": "NIO",
    "byd": "BYD",
    "mclaren": "McLaren",
}


def slugify(value: str) -> str:
    value = (
        value.lower()
        .replace(" ", "-")
        .replace(".", "")
        .replace("&", "und")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace("/", "-")
        .replace("(", "")
        .replace(")", "")
    )
    return re.sub(r"[^a-z0-9-]+", "", value).strip("-")[:80]


def _cache_path(*parts: str) -> Path:
    return CACHE_DIR.joinpath(*parts)


def _read_cache(path: Path) -> dict | list | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_html(path: str) -> str | None:
    url = path if path.startswith("http") else f"{BASE_URL}{path}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "de,en;q=0.9"},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def _clean_title(title: str) -> str:
    title = unescape(title).strip()
    for suffix in (
        " - Technical Specs, Fuel consumption, Dimensions",
        " | Technical Specs, Fuel consumption, Dimensions",
        " - Technische Daten, Verbrauch, Abmessungen",
    ):
        if title.endswith(suffix):
            title = title[: -len(suffix)].strip()
    return title


def brand_label_from_path(path: str) -> str:
    """z. B. /en/volkswagen-brand-80 → Volkswagen."""
    slug = path.split(f"/{LOCALE}/")[-1].split("-brand-")[0]
    if slug in BRAND_LABEL_OVERRIDES:
        return BRAND_LABEL_OVERRIDES[slug]
    return slug.replace("-", " ").title()


def model_label_from_title(title: str, brand_label: str) -> str:
    label = _clean_title(title)
    for prefix in (brand_label + " ", "Volkswagen " if brand_label == "VW" else ""):
        if prefix and label.startswith(prefix):
            label = label[len(prefix) :].strip()
    return label or brand_label


def parse_brands(html: str) -> list[dict]:
    brands: list[dict] = []
    seen: set[str] = set()
    for path, brand_id, title in BRAND_LINK_RE.findall(html):
        if path in seen:
            continue
        seen.add(path)
        label = brand_label_from_path(path)
        brands.append(
            {
                "id": brand_id,
                "path": path,
                "slug": slugify(label),
                "label": label,
            }
        )
    brands.sort(key=lambda b: b["label"].lower())
    return brands


def parse_models(html: str, brand: dict) -> list[dict]:
    models: list[dict] = []
    seen: set[str] = set()
    brand_label = brand["label"]
    for path, model_id, title in MODEL_LINK_RE.findall(html):
        if path in seen:
            continue
        seen.add(path)
        label = model_label_from_title(title, brand_label)
        models.append(
            {
                "id": model_id,
                "path": path,
                "slug": slugify(label) or slugify(path),
                "label": label,
            }
        )
    models.sort(key=lambda m: m["label"].lower())
    return models


def parse_generations(html: str, model: dict) -> list[dict]:
    generations: list[dict] = []
    seen: set[str] = set()
    for path, gen_id, title in GENERATION_LINK_RE.findall(html):
        if path in seen:
            continue
        seen.add(path)
        label = _clean_title(title)
        generations.append(
            {
                "id": gen_id,
                "path": path,
                "slug": slugify(label) or f"generation-{gen_id}",
                "label": label,
            }
        )
    return generations


def parse_trims(html: str) -> list[dict]:
    trims: list[dict] = []
    seen: set[str] = set()
    for name, years in TRIM_RE.findall(html):
        name = unescape(re.sub(r"\s+", " ", name)).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        years = unescape(years or "").strip()
        label = name
        if years:
            label = f"{name} ({years})"
        hp_match = re.search(r"(\d+)\s*Hp", name, re.IGNORECASE)
        fuel = ""
        lower = name.lower()
        if "diesel" in lower or "tdi" in lower or "hdi" in lower or "dci" in lower:
            fuel = "diesel"
        elif "electric" in lower or "e-golf" in lower or re.search(r"\bev\b", lower):
            fuel = "elektro"
        elif "hybrid" in lower or "phev" in lower or "gte" in lower:
            fuel = "hybrid"
        elif "tsi" in lower or "benzin" in lower or re.search(r"\d\.\d", name):
            fuel = "benzin"
        entry: dict = {"label": label}
        if hp_match:
            entry["hp"] = int(hp_match.group(1))
        if fuel:
            entry["fuel"] = fuel
        trims.append(entry)
    return trims


def get_all_brands(*, fetch: bool = True) -> list[dict]:
    cache_file = _cache_path("brands.json")
    cached = _read_cache(cache_file)
    if isinstance(cached, list) and cached:
        return cached
    if not fetch:
        return cached if isinstance(cached, list) else []

    html = fetch_html(f"/{LOCALE}/allbrands")
    if html is None:
        return []
    brands = parse_brands(html)
    _write_cache(cache_file, brands)
    time.sleep(FETCH_DELAY_SEC)
    return brands


def get_models(brand: dict, *, fetch: bool = True) -> list[dict]:
    cache_file = _cache_path("models", f"{brand['slug']}.json")
    cached = _read_cache(cache_file)
    if isinstance(cached, list) and cached:
        return cached
    if not fetch:
        return cached if isinstance(cached, list) else []

    html = fetch_html(brand["path"])
    if html is None:
        _write_cache(cache_file, [])
        return []
    models = parse_models(html, brand)
    _write_cache(cache_file, models)
    time.sleep(FETCH_DELAY_SEC)
    return models


def get_generations(model: dict, brand: dict, *, fetch: bool = True) -> list[dict]:
    cache_key = slugify(model["path"].replace("/", "-"))
    cache_file = _cache_path("generations", brand["slug"], f"{cache_key}.json")
    cached = _read_cache(cache_file)
    if isinstance(cached, list) and cached:
        return cached
    if not fetch:
        return cached if isinstance(cached, list) else []

    html = fetch_html(model["path"])
    if html is None:
        _write_cache(cache_file, [])
        return []
    generations = parse_generations(html, model)
    _write_cache(cache_file, generations)
    time.sleep(FETCH_DELAY_SEC)
    return generations


def get_trims(generation: dict, *, fetch: bool = True) -> list[dict]:
    cache_file = _cache_path("trims", f"{generation['id']}.json")
    cached = _read_cache(cache_file)
    if isinstance(cached, list) and cached:
        return cached
    if not fetch:
        return cached if isinstance(cached, list) else []

    html = fetch_html(generation["path"])
    if html is None:
        _write_cache(cache_file, [])
        return []
    trims = parse_trims(html)
    _write_cache(cache_file, trims)
    time.sleep(FETCH_DELAY_SEC)
    return trims


def get_engines_for_generation(generation: dict, *, fetch: bool = False) -> list[dict]:
    trims = get_trims(generation, fetch=fetch)
    if not trims:
        return GENERIC_ENGINES
    engines = [{"label": t["label"], **{k: v for k, v in t.items() if k != "label"}} for t in trims]
    engines.append({"label": "Sonstige Motorisierung (bitte in Nachricht ergänzen)"})
    return engines
