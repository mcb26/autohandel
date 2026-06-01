"""Ausstattungs-Extras für Fahrzeuganfragen."""

VEHICLE_EXTRAS_CHOICES = [
    ("abgedunkelte_scheiben", "Abgedunkelte Scheiben"),
    ("abs", "ABS"),
    ("abstandswarner", "Abstandswarner"),
    ("adaptives_fahrwerk", "Adaptives Fahrwerk"),
    ("adaptives_kurvenlicht", "Adaptives Kurvenlicht"),
    ("allwetterreifen", "Allwetterreifen"),
    ("beheizbare_frontscheibe", "Beheizbare Frontscheibe"),
    ("behindertengerecht", "Behindertengerecht"),
    ("berganfahrassistent", "Berganfahrassistent"),
    ("bi_xenon", "Bi-Xenon Scheinwerfer"),
    ("blendfreies_fernlicht", "Blendfreies Fernlicht"),
    ("dachreling", "Dachreling"),
    ("elektr_heckklappe", "Elektr. Heckklappe"),
    ("elektr_wegfahrsperre", "Elektr. Wegfahrsperre"),
    ("esp", "ESP"),
    ("faltdach", "Faltdach"),
    ("fernlichtassistent", "Fernlichtassistent"),
    ("geschwindigkeitsbegrenzer", "Geschwindigkeitsbegrenzer"),
    ("kurvenlicht", "Kurvenlicht"),
    ("laserlicht", "Laserlicht"),
    ("led_scheinwerfer", "LED-Scheinwerfer"),
    ("led_tagfahrlicht", "LED-Tagfahrlicht"),
    ("leichtmetallfelgen", "Leichtmetallfelgen"),
    ("lichtsensor", "Lichtsensor"),
    ("luftfederung", "Luftfederung"),
    ("nachtsicht_assistent", "Nachtsicht-Assistent"),
    ("nebelscheinwerfer", "Nebelscheinwerfer"),
    ("notbremsassistent", "Notbremsassistent"),
    ("notrad", "Notrad"),
    ("pannenkit", "Pannenkit"),
    ("panorama_dach", "Panorama-Dach"),
    ("regensensor", "Regensensor"),
    ("reifendruckkontrolle", "Reifendruckkontrolle"),
    ("reserverad", "Reserverad"),
    ("scheinwerferreinigung", "Scheinwerferreinigung"),
    ("schiebedach", "Schiebedach"),
    ("keyless", "Schlüssellose Zentralverriegelung (Keyless)"),
    ("servolenkung", "Servolenkung"),
    ("sommerreifen", "Sommerreifen"),
    ("sportfahrwerk", "Sportfahrwerk"),
    ("sportpaket", "Sportpaket"),
    ("spurhalteassistent", "Spurhalteassistent"),
    ("stahlfelgen", "Stahlfelgen"),
    ("start_stopp", "Start/Stopp-Automatik"),
    ("tagfahrlicht", "Tagfahrlicht"),
    ("totwinkel_assistent", "Totwinkel-Assistent"),
    ("traktionskontrolle", "Traktionskontrolle"),
    ("verkehrszeichenerkennung", "Verkehrszeichenerkennung"),
    ("winterpaket", "Winterpaket"),
    ("winterreifen", "Winterreifen"),
    ("xenonscheinwerfer", "Xenonscheinwerfer"),
    ("zentralverriegelung", "Zentralverriegelung"),
]

VEHICLE_EXTRAS_LABELS = dict(VEHICLE_EXTRAS_CHOICES)
VALID_EXTRA_KEYS = frozenset(VEHICLE_EXTRAS_LABELS.keys())

VEHICLE_EXTRAS_GROUPS = [
    (
        "Sicherheit & Assistenz",
        [
            "abs",
            "esp",
            "notbremsassistent",
            "abstandswarner",
            "spurhalteassistent",
            "totwinkel_assistent",
            "verkehrszeichenerkennung",
            "traktionskontrolle",
            "berganfahrassistent",
            "geschwindigkeitsbegrenzer",
            "nachtsicht_assistent",
            "blendfreies_fernlicht",
            "fernlichtassistent",
            "elektr_wegfahrsperre",
            "start_stopp",
            "behindertengerecht",
        ],
    ),
    (
        "Beleuchtung",
        [
            "xenonscheinwerfer",
            "bi_xenon",
            "led_scheinwerfer",
            "laserlicht",
            "led_tagfahrlicht",
            "tagfahrlicht",
            "kurvenlicht",
            "adaptives_kurvenlicht",
            "nebelscheinwerfer",
            "lichtsensor",
            "scheinwerferreinigung",
        ],
    ),
    (
        "Komfort & Karosserie",
        [
            "keyless",
            "zentralverriegelung",
            "servolenkung",
            "regensensor",
            "beheizbare_frontscheibe",
            "abgedunkelte_scheiben",
            "elektr_heckklappe",
            "schiebedach",
            "panorama_dach",
            "faltdach",
            "dachreling",
        ],
    ),
    (
        "Fahrwerk & Pakete",
        [
            "sportfahrwerk",
            "adaptives_fahrwerk",
            "luftfederung",
            "sportpaket",
            "winterpaket",
        ],
    ),
    (
        "Räder & Reifen",
        [
            "leichtmetallfelgen",
            "stahlfelgen",
            "sommerreifen",
            "winterreifen",
            "allwetterreifen",
            "notrad",
            "reserverad",
            "pannenkit",
            "reifendruckkontrolle",
        ],
    ),
]


def build_vehicle_extras_groups(form):
    """Gruppierte Extras mit gebundenen Checkbox-Widgets für das Template."""
    widget_map = {
        subwidget.data["value"]: subwidget
        for subwidget in form["vehicle_extras"].subwidgets
    }
    groups = []
    for title, keys in VEHICLE_EXTRAS_GROUPS:
        items = []
        for key in keys:
            subwidget = widget_map.get(key)
            if subwidget is None:
                continue
            items.append(
                {
                    "key": key,
                    "label": VEHICLE_EXTRAS_LABELS[key],
                    "widget": subwidget,
                }
            )
        if items:
            groups.append({"title": title, "items": items})
    return groups


def build_vehicle_features_fields(form):
    """Merkmal-Felder mit Metadaten für das Template."""
    from .vehicle_features import VEHICLE_FEATURES_META

    fields = []
    for meta in VEHICLE_FEATURES_META:
        name = meta["name"]
        if name not in form.fields:
            continue
        fields.append({**meta, "field": form[name]})
    return fields
