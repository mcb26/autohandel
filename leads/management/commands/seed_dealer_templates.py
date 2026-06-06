from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from leads.models import DealerDocumentTemplate

TEMPLATE_FILES = {
    DealerDocumentTemplate.TYPE_PURCHASE_CONTRACT: "purchase_contract.docx",
    DealerDocumentTemplate.TYPE_INVOICE_EMAIL: "invoice_email.docx",
}


class Command(BaseCommand):
    help = "Lädt die mitgelieferten Kaufvertrag- und Rechnung/E-Mail-Vorlagen in die Datenbank."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Bestehende Vorlagen ersetzen.",
        )

    def handle(self, *args, **options):
        data_dir = Path(__file__).resolve().parents[2] / "data" / "document_templates"
        force = options["force"]
        created = 0
        updated = 0

        for template_type, filename in TEMPLATE_FILES.items():
            source = data_dir / filename
            if not source.is_file():
                self.stderr.write(self.style.ERROR(f"Datei fehlt: {source}"))
                continue

            existing = DealerDocumentTemplate.objects.filter(template_type=template_type).first()
            if existing and not force:
                self.stdout.write(
                    f"Übersprungen ({existing.get_template_type_display()}): bereits vorhanden."
                )
                continue

            content = source.read_bytes()
            if existing:
                if existing.file:
                    existing.file.delete(save=False)
                existing.file.save(filename, ContentFile(content), save=False)
                existing.original_filename = filename
                existing.uploaded_by = None
                existing.save()
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Aktualisiert: {existing.get_template_type_display()}"))
                continue

            obj = DealerDocumentTemplate(
                template_type=template_type,
                original_filename=filename,
            )
            obj.file.save(filename, ContentFile(content), save=True)
            created += 1
            self.stdout.write(self.style.SUCCESS(f"Angelegt: {obj.get_template_type_display()}"))

        self.stdout.write(self.style.SUCCESS(f"Fertig. Neu: {created}, aktualisiert: {updated}."))
