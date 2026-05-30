import logging
import time
import zipfile
from io import BytesIO
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.mail import send_mail
from django import forms
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .dashboard_filters import (
    ARCHIVE_VIEW_ACTIVE,
    ARCHIVE_VIEW_ALL,
    ARCHIVE_VIEW_ARCHIVED,
    DASHBOARD_PAGE_SIZE,
    adjacent_lead_pks,
    build_dashboard_queryset,
    dashboard_kpis,
    filters_from_request,
    list_query_string,
)
from .forms import CarLeadForm
from .models import CarLead, CarLeadImage

logger = logging.getLogger(__name__)

HOME_FORM_SESSION_KEY = "leads_form_loaded_at"
THANK_YOU_SESSION_KEY = "leads_thank_you_summary"
MIN_FORM_SECONDS = 3
RATE_LIMIT_MAX_SUCCESS = 5
RATE_LIMIT_WINDOW_SECONDS = 60 * 60
GENERIC_FORM_ERROR = "Ihre Anfrage konnte nicht verarbeitet werden. Bitte versuchen Sie es später erneut."


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _rate_limit_cache_key(ip: str | None) -> str:
    safe_ip = ip or "unknown"
    return f"leads:rate:{safe_ip}"


def _send_dealer_mail(lead):
    if not settings.DEALER_NOTIFICATION_EMAIL:
        return

    subject = f"Neue Fahrzeuganfrage: {lead.vehicle_summary()}"
    message = (
        f"Neue Fahrzeugankauf-Anfrage\n\n"
        f"Name: {lead.customer_name}\n"
        f"E-Mail: {lead.email}\n"
        f"Telefon: {lead.phone}\n"
        f"Fahrzeug: {lead.vehicle_summary()}\n"
        f"Modellreihe: {lead.model}\n"
        f"Baureihe: {lead.series or '-'}\n"
        f"Motorisierung: {lead.engine or '-'}\n"
        f"Erstzulassung: {lead.first_registration_display}\n"
        f"Kilometerstand: {lead.mileage}\n"
        f"Zustand: {lead.vehicle_condition}\n"
        f"Preisvorstellung: {lead.expected_price or '-'}\n"
        f"PLZ: {lead.postal_code}\n"
        f"Nachricht: {lead.message or '-'}\n"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.DEALER_NOTIFICATION_EMAIL],
        fail_silently=True,
    )


def home(request):
    ip = _get_client_ip(request)
    if request.method == "POST":
        form = CarLeadForm(request.POST, request.FILES)
        if form.is_valid():
            # Honeypot (wird auch in Form-Validation gesetzt, hier nochmal mit Logging/UX)
            if (form.cleaned_data.get("website") or "").strip():
                logger.warning("Spam blockiert (honeypot). ip=%s", ip)
                form.add_error(None, GENERIC_FORM_ERROR)
                return render(request, "home.html", {"form": form})

            # Zeitprüfung: muss mindestens MIN_FORM_SECONDS dauern
            loaded_at = request.session.get(HOME_FORM_SESSION_KEY)
            if not loaded_at:
                logger.warning("Spam blockiert (missing session timestamp). ip=%s", ip)
                form.add_error(None, GENERIC_FORM_ERROR)
                return render(request, "home.html", {"form": form})
            if time.time() - float(loaded_at) < MIN_FORM_SECONDS:
                logger.warning("Spam blockiert (too fast). ip=%s", ip)
                form.add_error(None, GENERIC_FORM_ERROR)
                return render(request, "home.html", {"form": form})

            # Rate limiting: max. 5 erfolgreiche Saves pro IP / 60 Minuten
            key = _rate_limit_cache_key(ip)
            current = int(cache.get(key, 0))
            if current >= RATE_LIMIT_MAX_SUCCESS:
                logger.warning("Spam/RateLimit blockiert (limit reached). ip=%s", ip)
                form.add_error(None, GENERIC_FORM_ERROR)
                return render(request, "home.html", {"form": form})

            lead = form.save(commit=False)
            lead.source_ip = ip
            lead.user_agent = request.META.get("HTTP_USER_AGENT", "")[:1000]
            lead.save()
            for image_file in form.cleaned_data.get("images", []):
                CarLeadImage.objects.create(lead=lead, image=image_file)
            cache.set(key, current + 1, timeout=RATE_LIMIT_WINDOW_SECONDS)
            _send_dealer_mail(lead)
            request.session.pop(HOME_FORM_SESSION_KEY, None)
            request.session[THANK_YOU_SESSION_KEY] = lead.thank_you_summary()
            return redirect(reverse("leads:thank_you"))
    else:
        form = CarLeadForm()
        request.session[HOME_FORM_SESSION_KEY] = time.time()

    return render(request, "home.html", {"form": form})


def thank_you(request):
    summary = request.session.pop(THANK_YOU_SESSION_KEY, None)
    return render(request, "thank_you.html", {"summary": summary})


def privacy(request):
    return render(request, "privacy.html")


def imprint(request):
    return render(request, "imprint.html")


class DashboardLoginView(auth_views.LoginView):
    template_name = "dashboard/login.html"

    def get_success_url(self):
        return reverse("leads:dashboard_home")


class DashboardLogoutView(auth_views.LogoutView):
    next_page = "leads:dashboard_login"


class LeadStatusForm(forms.Form):
    status = forms.ChoiceField(choices=CarLead.STATUS_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].widget.attrs.update({"class": "form-select"})


class LeadNotesForm(forms.Form):
    internal_notes = forms.CharField(
        required=False,
        label="Interne Notizen",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "z. B. Rückruf Freitag 14 Uhr",
            }
        ),
    )


def _dashboard_list_context(request, page_obj) -> dict:
    filters = filters_from_request(request)
    return {
        "leads": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": page_obj.paginator,
        "list_query": list_query_string(request),
        "kpis": dashboard_kpis(),
        "q": filters["q"],
        "f_status": filters["f_status"],
        "f_brand": filters["f_brand"],
        "f_model": filters["f_model"],
        "f_created_from": filters["f_created_from"],
        "f_created_to": filters["f_created_to"],
        "f_reg_from": filters["f_reg_from"],
        "f_reg_to": filters["f_reg_to"],
        "f_km_min": filters["f_km_min_display"],
        "f_km_max": filters["f_km_max_display"],
        "f_price_min": filters["f_price_min_display"],
        "f_price_max": filters["f_price_max_display"],
        "sort": filters["sort"],
        "dir": filters["dir"],
        "archive_view": filters["archive_view"],
        "archive_view_choices": [
            (ARCHIVE_VIEW_ACTIVE, "Aktive Anfragen"),
            (ARCHIVE_VIEW_ARCHIVED, "Archiv"),
            (ARCHIVE_VIEW_ALL, "Alle"),
        ],
        "status_choices": CarLead.STATUS_CHOICES,
    }


@login_required
def dashboard_home(request):
    queryset = build_dashboard_queryset(request)
    paginator = Paginator(queryset, DASHBOARD_PAGE_SIZE)
    page_number = request.GET.get("page", "1")
    page_obj = paginator.get_page(page_number)
    context = _dashboard_list_context(request, page_obj)
    return render(request, "dashboard/lead_list.html", context)


def _archive_redirect_query(request) -> str:
    view = request.GET.get("view") or request.POST.get("view") or ARCHIVE_VIEW_ACTIVE
    if view == ARCHIVE_VIEW_ARCHIVED:
        return f"?view={ARCHIVE_VIEW_ARCHIVED}"
    return ""


@login_required
@require_POST
def dashboard_lead_archive(request, pk: int):
    lead = get_object_or_404(CarLead, pk=pk)
    if not lead.is_archived:
        lead.is_archived = True
        lead.archived_at = timezone.now()
        lead.save(update_fields=["is_archived", "archived_at", "updated_at"])
        messages.success(request, f"Anfrage #{lead.pk} wurde ins Archiv verschoben.")
    return redirect(f"{reverse('leads:dashboard_home')}{_archive_redirect_query(request)}")


@login_required
@require_POST
def dashboard_lead_unarchive(request, pk: int):
    lead = get_object_or_404(CarLead, pk=pk)
    if lead.is_archived:
        lead.is_archived = False
        lead.archived_at = None
        lead.save(update_fields=["is_archived", "archived_at", "updated_at"])
        messages.success(request, f"Anfrage #{lead.pk} wurde wiederhergestellt.")
    return redirect(reverse("leads:dashboard_lead_detail", kwargs={"pk": lead.pk}))


@login_required
@require_POST
def dashboard_lead_delete(request, pk: int):
    lead = get_object_or_404(CarLead, pk=pk)
    lead_id = lead.pk
    customer = lead.customer_name
    lead.delete()
    messages.success(request, f"Anfrage #{lead_id} ({customer}) wurde endgültig gelöscht.")
    return redirect(f"{reverse('leads:dashboard_home')}{_archive_redirect_query(request)}")


@login_required
def dashboard_lead_detail(request, pk: int):
    lead = get_object_or_404(CarLead, pk=pk)
    list_query = list_query_string(request)
    prev_pk, next_pk = adjacent_lead_pks(request, lead.pk)

    if request.method == "POST":
        action = (request.POST.get("action") or "status").strip()
        if action == "notes":
            notes_form = LeadNotesForm(request.POST)
            if notes_form.is_valid():
                lead.internal_notes = notes_form.cleaned_data["internal_notes"]
                lead.save(update_fields=["internal_notes", "updated_at"])
                messages.success(request, "Interne Notizen wurden gespeichert.")
                return redirect(f"{reverse('leads:dashboard_lead_detail', kwargs={'pk': lead.pk})}{list_query}")
        else:
            status_form = LeadStatusForm(request.POST)
            if status_form.is_valid():
                lead.status = status_form.cleaned_data["status"]
                lead.save(update_fields=["status", "updated_at"])
                messages.success(request, "Status wurde erfolgreich aktualisiert.")
                return redirect(f"{reverse('leads:dashboard_lead_detail', kwargs={'pk': lead.pk})}{list_query}")

    status_form = LeadStatusForm(initial={"status": lead.status})
    notes_form = LeadNotesForm(initial={"internal_notes": lead.internal_notes})

    image_urls = [img.image.url for img in lead.images.all() if img.image]

    return render(
        request,
        "dashboard/lead_detail.html",
        {
            "lead": lead,
            "status_form": status_form,
            "notes_form": notes_form,
            "archive_view": request.GET.get("view", ""),
            "list_query": list_query,
            "prev_lead_pk": prev_pk,
            "next_lead_pk": next_pk,
            "image_urls": image_urls,
        },
    )


@login_required
def dashboard_lead_print(request, pk: int):
    lead = get_object_or_404(CarLead, pk=pk)
    include_images = request.GET.get("images", "1") == "1"
    return render(
        request,
        "dashboard/lead_print.html",
        {"lead": lead, "include_images": include_images},
    )


@login_required
def dashboard_lead_package_download(request, pk: int):
    lead = get_object_or_404(CarLead, pk=pk)
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
