import zipfile
from io import BytesIO
from urllib.parse import quote

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.text import slugify

from .models import CarLead, CarLeadImage


class CarLeadImageInline(admin.TabularInline):
    model = CarLeadImage
    extra = 0
    fields = ("image", "image_preview", "created_at")
    readonly_fields = ("image_preview", "created_at")

    @admin.display(description="Vorschau")
    def image_preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<a href="{0}" target="_blank"><img src="{0}" style="height:70px;border-radius:4px;" /></a>',
                obj.image.url,
            )
        return "-"


@admin.register(CarLead)
class CarLeadAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "customer_name",
        "brand",
        "model",
        "mileage",
        "phone",
        "email",
        "status",
        "is_archived",
    )
    list_filter = ("status", "is_archived", "created_at")
    search_fields = ("customer_name", "email", "phone", "brand", "model", "series", "engine")
    readonly_fields = ("created_at", "updated_at", "source_ip", "user_agent", "download_package_link")
    list_per_page = 25
    inlines = [CarLeadImageInline]

    fieldsets = (
        (
            "Lead",
            {
                "fields": (
                    "status",
                    "is_archived",
                    "archived_at",
                    "created_at",
                    "updated_at",
                    "download_package_link",
                )
            },
        ),
        (
            "Fahrzeugdaten",
            {
                "fields": (
                    "brand",
                    "model",
                    "series",
                    "engine",
                    "internal_notes",
                    "first_registration",
                    "mileage",
                    "vehicle_condition",
                    "expected_price",
                )
            },
        ),
        (
            "Kundendaten",
            {
                "fields": (
                    "customer_name",
                    "email",
                    "phone",
                    "postal_code",
                    "message",
                    "privacy_accepted",
                    "marketing_consent",
                )
            },
        ),
        ("Technik", {"fields": ("source_ip", "user_agent")}),
    )

    @admin.display(description="Bilderpaket")
    def download_package_link(self, obj):
        if not obj.pk:
            return "Verfügbar nach dem ersten Speichern."
        url = reverse("admin:leads_carlead_download_package", args=[obj.pk])
        return format_html('<a class="button" href="{}">Als ZIP herunterladen</a>', url)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:lead_id>/download-package/",
                self.admin_site.admin_view(self.download_package_view),
                name="leads_carlead_download_package",
            ),
        ]
        return custom_urls + urls

    def download_package_view(self, request, lead_id):
        lead = self.get_object(request, lead_id)
        if lead is None:
            return HttpResponse("Lead nicht gefunden.", status=404)

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            lead_data = (
                f"Lead-ID: {lead.pk}\n"
                f"Eingang: {lead.created_at}\n"
                f"Status: {lead.get_status_display()}\n"
                f"\nKundendaten\n"
                f"Name: {lead.customer_name}\n"
                f"E-Mail: {lead.email}\n"
                f"Telefon: {lead.phone}\n"
                f"PLZ: {lead.postal_code}\n"
                f"\nFahrzeugdaten\n"
                f"Marke: {lead.brand}\n"
                f"Modellreihe: {lead.model}\n"
                f"Baureihe: {lead.series or '-'}\n"
                f"Motorisierung: {lead.engine or '-'}\n"
                f"Erstzulassung: {lead.first_registration_display}\n"
                f"Kilometerstand: {lead.mileage}\n"
                f"Zustand: {lead.get_vehicle_condition_display()}\n"
                f"Preisvorstellung: {lead.expected_price or '-'}\n"
                f"\nInterne Notizen\n{lead.internal_notes or '-'}\n"
                f"\nNachricht\n{lead.message or '-'}\n"
            )
            archive.writestr("angebot.txt", lead_data)
            for idx, image in enumerate(lead.images.all(), start=1):
                if not image.image:
                    continue
                original_name = image.image.name.split("/")[-1]
                extension = original_name.split(".")[-1] if "." in original_name else "jpg"
                filename = f"bilder/{idx:02d}.{extension}"
                try:
                    archive.writestr(filename, image.image.read())
                except Exception:
                    continue

        buffer.seek(0)
        filename = f"lead-{lead.pk}-{slugify(lead.customer_name) or 'kunde'}.zip"
        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(filename)}"
        return response
