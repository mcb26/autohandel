"""Word-Vorlagen (.docx) mit Platzhaltern für Lead-Dokumente."""

from __future__ import annotations

import io
import logging
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import CarLead, DealerDocumentTemplate

logger = logging.getLogger(__name__)

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

PLACEHOLDER_HELP_CONTRACT = [
    ("{{ verkaeufer_name }}", "Verkäufer (Kunde / Privatperson)"),
    ("{{ verkaeufer_plz }}", "PLZ des Verkäufers"),
    ("{{ kaeufer_name }}", "Käufer (Ihre Firma)"),
    ("{{ kaeufer_adresse }}", "Adresse des Käufers (Firma)"),
    ("{{ vertragspartner_kunde }}", "Name des Kunden (wie Verkäufer)"),
    ("{{ vertragspartner_firma }}", "Name Ihrer Firma (wie Käufer)"),
    ("{{ auto }}", "Fahrzeugkurztext"),
    ("{{ auto_beschreibung }}", "Fahrzeug in einem Satz (Marke, EZ, km, …)"),
    ("{{ auto_beschreibung_lang }}", "Fahrzeug ausführlich (mehrzeilig)"),
    ("{{ vertragsgegenstand }}", "Vertragsgegenstand fertig formuliert"),
    ("{{ angebots_nummer }}", "Angebotsnummer (z. B. APG-42)"),
    ("{{ rechnungsnummer }}", "Rechnungsnummer mit Datum"),
]

PLACEHOLDER_HELP_DETAILS = [
    ("{{ kunde_name }}", "Name des Kunden"),
    ("{{ kunde_email }}", "E-Mail des Kunden"),
    ("{{ kunde_telefon }}", "Telefon des Kunden"),
    ("{{ kunde_plz }}", "PLZ des Kunden"),
    ("{{ marke }}", "Fahrzeugmarke"),
    ("{{ modell }}", "Modellreihe"),
    ("{{ baureihe }}", "Baureihe / Generation"),
    ("{{ motorisierung }}", "Motorisierung"),
    ("{{ fahrzeug }}", "Fahrzeugkurztext (Marke · Modell · …)"),
    ("{{ erstzulassung }}", "Erstzulassung (MM/JJJJ)"),
    ("{{ tuv_bis }}", "TÜV bis (MM/JJJJ)"),
    ("{{ kilometerstand }}", "Kilometerstand (formatiert)"),
    ("{{ kraftstoff }}", "Kraftstoffart"),
    ("{{ farbe }}", "Fahrzeugfarbe"),
    ("{{ zustand }}", "Fahrzeugzustand"),
    ("{{ angemeldet }}", "Angemeldet (Ja/Nein)"),
    ("{{ preisvorstellung }}", "Preisvorstellung (EUR, formatiert)"),
    ("{{ merkmale }}", "Ausgewählte Fahrzeugmerkmale"),
    ("{{ extras }}", "Ausgewählte Extras"),
    ("{{ nachricht }}", "Kundennachricht"),
    ("{{ interne_notizen }}", "Interne Händler-Notizen"),
    ("{{ lead_id }}", "Lead-Nummer"),
    ("{{ datum_heute }}", "Heutiges Datum (TT.MM.JJJJ)"),
    ("{{ firma_name }}", "Firmenname"),
    ("{{ firma_adresse }}", "Firmenadresse"),
    ("{{ firma_telefon }}", "Firmentelefon"),
    ("{{ firma_email }}", "Firmen-E-Mail"),
]

PLACEHOLDER_HELP = [*PLACEHOLDER_HELP_CONTRACT, *PLACEHOLDER_HELP_DETAILS]


def _format_eur(value: Decimal | None) -> str:
    if value is None:
        return ""
    quantized = value.quantize(Decimal("0.01"))
    text = f"{quantized:,.2f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def _format_mileage(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _build_auto_beschreibung(lead: CarLead) -> str:
    parts = [lead.vehicle_summary()]
    parts.append(f"EZ {lead.first_registration_display}")
    parts.append(f"{_format_mileage(lead.mileage)} km")
    if lead.fuel_type:
        parts.append(lead.get_fuel_type_display())
    if lead.vehicle_color:
        parts.append(lead.get_vehicle_color_display())
    if lead.engine_technical_summary:
        parts.append(lead.engine_technical_summary)
    return ", ".join(parts)


def _build_auto_beschreibung_lang(lead: CarLead) -> str:
    lines = [
        f"Fahrzeug: {lead.vehicle_summary()}",
        f"Erstzulassung: {lead.first_registration_display}",
        f"TÜV bis: {lead.tuv_until_display}",
        f"Kilometerstand: {_format_mileage(lead.mileage)} km",
    ]
    if lead.fuel_type:
        lines.append(f"Kraftstoff: {lead.get_fuel_type_display()}")
    if lead.vehicle_color:
        lines.append(f"Farbe: {lead.get_vehicle_color_display()}")
    if lead.engine:
        lines.append(f"Motorisierung: {lead.engine}")
    if lead.engine_technical_summary:
        lines.append(f"Technik: {lead.engine_technical_summary}")
    lines.append(f"Zustand: {lead.get_vehicle_condition_display()}")
    if lead.is_registered:
        lines.append(f"Angemeldet: {lead.get_is_registered_display()}")
    return "\n".join(lines)


def build_lead_document_context(lead: CarLead) -> dict:
    auto_kurz = lead.vehicle_summary()
    auto_beschreibung = _build_auto_beschreibung(lead)
    auto_beschreibung_lang = _build_auto_beschreibung_lang(lead)
    verkaeufer_name = lead.customer_name
    kaeufer_name = settings.SITE_COMPANY_NAME
    vertragsgegenstand = (
        f"Der Verkäufer verkauft an den Käufer folgendes Fahrzeug: {auto_beschreibung}."
    )

    return {
        "lead_id": lead.pk,
        "verkaeufer_name": verkaeufer_name,
        "verkaeufer_plz": lead.postal_code,
        "kaeufer_name": kaeufer_name,
        "kaeufer_adresse": settings.SITE_ADDRESS,
        "vertragspartner_kunde": verkaeufer_name,
        "vertragspartner_firma": kaeufer_name,
        "auto": auto_kurz,
        "auto_beschreibung": auto_beschreibung,
        "auto_beschreibung_lang": auto_beschreibung_lang,
        "vertragsgegenstand": vertragsgegenstand,
        "kunde_name": lead.customer_name,
        "kunde_email": lead.email,
        "kunde_telefon": lead.phone,
        "kunde_plz": lead.postal_code,
        "marke": lead.brand,
        "modell": lead.model,
        "baureihe": lead.series or "",
        "motorisierung": lead.engine or "",
        "fahrzeug": lead.vehicle_summary(),
        "erstzulassung": lead.first_registration_display,
        "tuv_bis": lead.tuv_until_display,
        "kilometerstand": _format_mileage(lead.mileage),
        "kilometerstand_km": str(lead.mileage),
        "kraftstoff": lead.get_fuel_type_display() if lead.fuel_type else "",
        "farbe": lead.get_vehicle_color_display() if lead.vehicle_color else "",
        "zustand": lead.get_vehicle_condition_display(),
        "angemeldet": lead.get_is_registered_display() if lead.is_registered else "",
        "preisvorstellung": _format_eur(lead.expected_price),
        "preis_eur": str(lead.expected_price) if lead.expected_price is not None else "",
        "merkmale": ", ".join(lead.active_vehicle_features()) or "",
        "extras": ", ".join(lead.selected_vehicle_extras()) or "",
        "nachricht": lead.message or "",
        "interne_notizen": lead.internal_notes or "",
        "datum_heute": timezone.localdate().strftime("%d.%m.%Y"),
        "angebots_nummer": f"APG-{lead.pk}",
        "rechnungsnummer": f"APG-{lead.pk}-{timezone.localdate().strftime('%Y%m%d')}",
        "firma_name": settings.SITE_COMPANY_NAME,
        "firma_adresse": settings.SITE_ADDRESS,
        "firma_telefon": settings.SITE_PHONE,
        "firma_email": settings.SITE_EMAIL,
        "customer_name": lead.customer_name,
        "customer_email": lead.email,
        "customer_phone": lead.phone,
        "brand": lead.brand,
        "model": lead.model,
        "vehicle_summary": lead.vehicle_summary(),
        "today": timezone.localdate().strftime("%d.%m.%Y"),
    }


def validate_docx_upload(uploaded_file) -> None:
    name = (getattr(uploaded_file, "name", "") or "").lower()
    if not name.endswith(".docx"):
        raise ValidationError("Bitte eine Word-Datei (.docx) hochladen.")
    uploaded_file.seek(0)
    header = uploaded_file.read(4)
    uploaded_file.seek(0)
    if header != b"PK\x03\x04":
        raise ValidationError("Die Datei ist keine gültige .docx-Datei.")


def get_active_template(template_type: str) -> DealerDocumentTemplate | None:
    return DealerDocumentTemplate.objects.filter(template_type=template_type).first()


def render_lead_document(lead: CarLead, template_type: str) -> tuple[bytes, str]:
    template = get_active_template(template_type)
    if not template or not template.file:
        label = dict(DealerDocumentTemplate.TYPE_CHOICES).get(template_type, template_type)
        raise ValidationError(f"Es ist noch keine Vorlage für „{label}“ hochgeladen.")

    try:
        from docxtpl import DocxTemplate
    except ImportError as exc:
        raise ValidationError(
            "docxtpl ist nicht installiert. Bitte den Server mit venv starten: "
            "source venv/bin/activate && pip install -r requirements.txt "
            "oder: ./scripts/dev-server.sh"
        ) from exc

    template.file.open("rb")
    try:
        doc = DocxTemplate(template.file)
        context = build_lead_document_context(lead)
        doc.render(context)
        buffer = io.BytesIO()
        doc.save(buffer)
    except Exception as exc:
        logger.exception("Dokument konnte nicht erzeugt werden (Lead %s, Typ %s)", lead.pk, template_type)
        raise ValidationError(
            "Die Vorlage konnte nicht ausgefüllt werden. Prüfen Sie die Platzhalter in der .docx-Datei."
        ) from exc
    finally:
        template.file.close()

    type_labels = {
        DealerDocumentTemplate.TYPE_PURCHASE_CONTRACT: "Kaufvertrag",
        DealerDocumentTemplate.TYPE_INVOICE_EMAIL: "Rechnung_Email",
    }
    prefix = type_labels.get(template_type, "Dokument")
    safe_name = lead.customer_name.replace(" ", "_")[:40]
    filename = f"{prefix}_Lead{lead.pk}_{safe_name}.docx"
    return buffer.getvalue(), filename


def build_starter_template_docx(template_type: str) -> tuple[bytes, str]:
    try:
        from .docx_template_builder import build_starter_template_docx as _build
    except ImportError as exc:
        raise ValidationError("python-docx ist nicht installiert.") from exc
    return _build(template_type)
