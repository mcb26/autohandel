import re
from datetime import date, datetime

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .catalog_loader import get_brand_catalog, ordered_brand_choices
from .engine_specs import find_engine_in_catalog, parse_displacement_liters
from .models import CarLead
from .vehicle_extras import VALID_EXTRA_KEYS, VEHICLE_EXTRAS_CHOICES


class MonthYearInput(forms.TextInput):
    def __init__(self, attrs=None):
        defaults = {
            "inputmode": "numeric",
            "placeholder": "MM/JJ",
            "maxlength": "7",
            "autocomplete": "off",
            "class": "form-control lead-month-year-input",
            "aria-describedby": "id_first_registration_help",
        }
        if attrs:
            defaults.update(attrs)
        super().__init__(attrs=defaults)


def _two_digit_year(year_part: int) -> int:
    now = datetime.now()
    century = (now.year // 100) * 100
    year = century + year_part
    if year_part > (now.year % 100) + 1:
        year -= 100
    return year


def parse_month_year(value: str) -> date:
    raw = (value or "").strip()
    if not raw:
        raise ValidationError("Bitte dieses Feld ausfüllen.")

    digits = re.sub(r"\D", "", raw)
    if len(digits) == 4:
        month_s, year_s = digits[:2], digits[2:]
    else:
        match = re.match(r"^(\d{1,2})\s*[/.\-]\s*(\d{2}|\d{4})$", raw)
        if not match:
            raise ValidationError("Bitte Erstzulassung als MM/JJ eingeben (z. B. 03/21).")
        month_s, year_s = match.group(1), match.group(2)

    month = int(month_s)
    if month < 1 or month > 12:
        raise ValidationError("Bitte einen gültigen Monat (01–12) eingeben.")

    if len(year_s) == 4:
        year = int(year_s)
    else:
        year = _two_digit_year(int(year_s))

    max_year = datetime.now().year + 1
    if year < 1950 or year > max_year:
        raise ValidationError(f"Bitte ein Jahr zwischen 1950 und {max_year} eingeben.")

    return date(year, month, 1)


class MonthYearField(forms.Field):
    widget = MonthYearInput

    def __init__(self, **kwargs):
        kwargs.setdefault("label", "Erstzulassung (MM/JJ)")
        kwargs.setdefault(
            "help_text",
            "Format: MM/JJ — z. B. 03/21 für März 2021",
        )
        super().__init__(**kwargs)

    def prepare_value(self, value):
        if isinstance(value, date):
            return f"{value.month:02d}/{value.year % 100:02d}"
        return value or ""

    def to_python(self, value):
        if value in (None, ""):
            return None
        return parse_month_year(str(value))


class OptionalMonthYearField(MonthYearField):
    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def to_python(self, value):
        if value in (None, ""):
            return None
        return parse_month_year(str(value))


class TuvMonthYearInput(MonthYearInput):
    def __init__(self, attrs=None):
        defaults = {
            "inputmode": "numeric",
            "placeholder": "MM/JJ",
            "maxlength": "7",
            "autocomplete": "off",
            "class": "form-control lead-month-year-input lead-tuv-input",
            "aria-describedby": "id_tuv_until_help",
        }
        if attrs:
            defaults.update(attrs)
        super(MonthYearInput, self).__init__(attrs=defaults)


OptionalMonthYearField.widget = TuvMonthYearInput


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        cleaned_files = []
        for item in data:
            cleaned_files.append(super().clean(item, initial))
        return cleaned_files


class CarLeadForm(forms.ModelForm):
    website = forms.CharField(required=False, label="Website")
    brand = forms.ChoiceField(
        required=True,
        label="Fahrzeugmarke",
        choices=[("", "Bitte Marke auswählen")],
    )
    model = forms.ChoiceField(
        required=True,
        label="Modellreihe",
        choices=[("", "Bitte zuerst Marke auswählen")],
    )
    series = forms.ChoiceField(
        required=True,
        label="Baureihe / Generation",
        choices=[("", "Bitte zuerst Modellreihe auswählen")],
    )
    engine_choice = forms.ChoiceField(
        required=True,
        label="Ausstattung / Motorisierung",
        choices=[("", "Bitte zuerst Baureihe auswählen")],
    )
    images = MultipleFileField(
        required=False,
        label="Fahrzeugbilder (optional)",
        widget=MultipleFileInput(attrs={"multiple": True, "accept": "image/*"}),
    )
    postal_code = forms.CharField(
        label="PLZ",
        validators=[RegexValidator(r"^\d{5}$", "Bitte eine gültige 5-stellige PLZ eingeben.")],
    )
    first_registration = MonthYearField()
    tuv_until = OptionalMonthYearField(
        label="TÜV bis (MM/JJ)",
        help_text="Format: MM/JJ — z. B. 03/27 für März 2027",
    )
    fuel_type = forms.ChoiceField(
        required=True,
        label="Kraftstoffart",
        choices=[("", "Bitte Kraftstoff wählen")] + list(CarLead.FUEL_TYPE_CHOICES),
    )
    vehicle_extras = forms.MultipleChoiceField(
        required=False,
        label="Extras",
        choices=VEHICLE_EXTRAS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = CarLead
        fields = [
            "brand",
            "model",
            "series",
            "first_registration",
            "tuv_until",
            "fuel_type",
            "vehicle_color",
            "mileage",
            "vehicle_condition",
            "is_registered",
            "expected_price",
            "feature_maintenance",
            "feature_roadworthy",
            "feature_warranty",
            "feature_inspection_new",
            "feature_non_smoker",
            "feature_service_book",
            "customer_name",
            "email",
            "phone",
            "postal_code",
            "message",
            "privacy_accepted",
            "marketing_consent",
        ]
        labels = {
            "brand": "Fahrzeugmarke",
            "model": "Modellreihe",
            "series": "Baureihe / Generation",
            "engine": "Ausstattung / Motorisierung",
            "first_registration": "Erstzulassung",
            "tuv_until": "TÜV bis",
            "fuel_type": "Kraftstoffart",
            "vehicle_color": "Farbe",
            "mileage": "Kilometerstand",
            "vehicle_condition": "Fahrzeugzustand",
            "is_registered": "Fahrzeug angemeldet",
            "expected_price": "Preisvorstellung (EUR)",
            "feature_maintenance": "Wartung",
            "feature_roadworthy": "Fahrtauglich",
            "feature_warranty": "Garantie",
            "feature_inspection_new": "Inspektion neu",
            "feature_non_smoker": "Nichtraucher-Fahrzeug",
            "feature_service_book": "Scheckheftgepflegt",
            "customer_name": "Name",
            "email": "E-Mail",
            "phone": "Telefonnummer",
            "message": "Nachricht",
            "privacy_accepted": "Ich stimme der Verarbeitung meiner Daten gemäß Datenschutzerklärung zu.",
            "marketing_consent": "Ich möchte Informationen zu Angeboten per E-Mail erhalten.",
        }
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(
            [
                "brand",
                "model",
                "series",
                "engine_choice",
                "first_registration",
                "tuv_until",
                "fuel_type",
                "vehicle_color",
                "mileage",
                "vehicle_condition",
                "is_registered",
                "expected_price",
                "feature_maintenance",
                "feature_roadworthy",
                "feature_warranty",
                "feature_inspection_new",
                "feature_non_smoker",
                "feature_service_book",
                "vehicle_extras",
                "customer_name",
                "email",
                "phone",
                "postal_code",
                "message",
                "images",
                "privacy_accepted",
                "marketing_consent",
                "website",
            ]
        )
        required_fields = [
            "brand",
            "model",
            "series",
            "engine_choice",
            "first_registration",
            "tuv_until",
            "fuel_type",
            "vehicle_color",
            "mileage",
            "vehicle_condition",
            "is_registered",
            "expected_price",
            "customer_name",
            "email",
            "phone",
            "postal_code",
            "privacy_accepted",
        ]
        autocomplete_attrs = {
            "customer_name": "name",
            "email": "email",
            "phone": "tel",
            "postal_code": "postal-code",
            "first_registration": "off",
        }
        for field_name, field in self.fields.items():
            if field_name in required_fields:
                field.required = True
                field.error_messages["required"] = "Bitte dieses Feld ausfüllen."
            if field_name in autocomplete_attrs:
                field.widget.attrs.setdefault("autocomplete", autocomplete_attrs[field_name])
            if field_name in (
                "brand",
                "model",
                "series",
                "engine_choice",
                "first_registration",
                "tuv_until",
                "fuel_type",
                "vehicle_color",
                "is_registered",
                "customer_name",
                "email",
                "phone",
                "postal_code",
                "privacy_accepted",
            ):
                field.use_required_attribute = False
            if field_name == "images":
                field.widget.attrs["class"] = "visually-hidden images-file-input"
                field.widget.attrs["tabindex"] = "-1"
            elif isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
                field.widget.attrs["class"] = css_class
            elif isinstance(field.widget, forms.Select):
                if field_name in ("brand", "model", "series", "engine_choice"):
                    field.widget.attrs["class"] = "form-select catalog-select"
                else:
                    field.widget.attrs["class"] = "form-select"
            elif field_name == "first_registration":
                pass
            elif field_name == "tuv_until":
                pass
            else:
                css_class = "form-control"
                if field_name in ("customer_name", "email", "phone", "postal_code"):
                    css_class = f"{css_class} lead-contact-input"
                field.widget.attrs["class"] = css_class

        self.fields["brand"].choices = [("", "Bitte Marke auswählen")] + ordered_brand_choices()
        self.fields["model"].choices = [("", "Bitte zuerst Marke auswählen")]
        self.fields["series"].choices = [("", "Bitte zuerst Modellreihe auswählen")]
        self.fields["engine_choice"].choices = [("", "Bitte zuerst Baureihe auswählen")]
        self.fields["vehicle_condition"].choices = [("", "Bitte Zustand auswählen")] + list(
            CarLead.CONDITION_CHOICES
        )
        self.fields["is_registered"].choices = [("", "Bitte auswählen")] + list(CarLead.REGISTERED_CHOICES)
        self.fields["vehicle_color"].choices = [("", "Bitte Farbe wählen")] + list(CarLead.COLOR_CHOICES)

        if self.instance.pk and self.instance.vehicle_extras:
            self.initial.setdefault("vehicle_extras", self.instance.vehicle_extras)

        selected_brand = (self.data.get("brand") if self.is_bound else self.initial.get("brand")) or ""
        selected_model = (self.data.get("model") if self.is_bound else self.initial.get("model")) or ""
        selected_series = (self.data.get("series") if self.is_bound else self.initial.get("series")) or ""
        selected_engine = (
            self.data.get("engine_choice") if self.is_bound else self.initial.get("engine_choice")
        ) or ""

        brand_data = get_brand_catalog(selected_brand) if selected_brand else None
        if brand_data:
            models = brand_data.get("models", {})
            model_choices = [(m_key, m_value["label"]) for m_key, m_value in models.items()]
            self.fields["model"].choices = [("", "Bitte Modellreihe auswählen")] + model_choices

            if selected_model in models:
                series_map = models[selected_model].get("series", {})
                series_choices = [(s_key, s_value["label"]) for s_key, s_value in series_map.items()]
                self.fields["series"].choices = [("", "Bitte Baureihe auswählen")] + series_choices

                if selected_series in series_map:
                    engines = series_map[selected_series].get("engines", [])
                    engine_choices = [(eng["label"], eng["label"]) for eng in engines]
                    self.fields["engine_choice"].choices = [
                        ("", "Bitte Ausstattung / Motorisierung auswählen")
                    ] + engine_choices
                    if selected_engine:
                        self.fields["engine_choice"].initial = selected_engine

        for field_name in self.errors:
            if field_name not in self.fields:
                continue
            field = self.fields[field_name]
            css = field.widget.attrs.get("class", "")
            if "is-invalid" not in css.split():
                field.widget.attrs["class"] = f"{css} is-invalid".strip()

    def clean_privacy_accepted(self):
        accepted = self.cleaned_data.get("privacy_accepted")
        if not accepted:
            raise forms.ValidationError("Bitte akzeptieren Sie die Datenschutzerklärung.")
        return accepted

    def clean_website(self):
        value = (self.cleaned_data.get("website") or "").strip()
        return value

    def clean_images(self):
        files = self.cleaned_data.get("images", [])
        if len(files) > 10:
            raise forms.ValidationError("Bitte maximal 10 Bilder hochladen.")
        for file in files:
            content_type = getattr(file, "content_type", "") or ""
            if not content_type.startswith("image/"):
                raise forms.ValidationError("Bitte nur Bilddateien hochladen.")
            if file.size > 8 * 1024 * 1024:
                raise forms.ValidationError("Ein Bild darf maximal 8 MB groß sein.")
        return files

    def clean_vehicle_extras(self):
        selected = self.cleaned_data.get("vehicle_extras") or []
        return [key for key in selected if key in VALID_EXTRA_KEYS]

    def clean(self):
        cleaned_data = super().clean()
        brand_key = cleaned_data.get("brand")
        model_key = cleaned_data.get("model")
        series_key = cleaned_data.get("series")
        engine_choice = cleaned_data.get("engine_choice")

        brand_data = get_brand_catalog(brand_key) if brand_key else None
        if not brand_data:
            self.add_error("brand", "Bitte eine gültige Marke auswählen.")
            return cleaned_data

        models = brand_data.get("models", {})
        if not model_key or model_key not in models:
            self.add_error("model", "Bitte eine gültige Modellreihe auswählen.")
            return cleaned_data

        series_map = models[model_key].get("series", {})
        if not series_key or series_key not in series_map:
            self.add_error("series", "Bitte eine gültige Baureihe auswählen.")
            return cleaned_data

        engines = series_map[series_key].get("engines", [])
        valid_engine_labels = {eng["label"] for eng in engines}
        if not engine_choice or engine_choice not in valid_engine_labels:
            self.add_error("engine_choice", "Bitte eine gültige Ausstattung / Motorisierung auswählen.")
            return cleaned_data

        cleaned_data["brand"] = brand_data.get("label", brand_key)
        cleaned_data["model"] = models[model_key]["label"]
        cleaned_data["series"] = series_map[series_key]["label"]
        cleaned_data["engine"] = engine_choice

        engine_entry = find_engine_in_catalog(brand_data, model_key, series_key, engine_choice)
        if engine_entry.get("hp"):
            cleaned_data["engine_hp"] = engine_entry["hp"]
        displacement = engine_entry.get("displacement") or parse_displacement_liters(engine_choice)
        if displacement:
            cleaned_data["engine_displacement"] = displacement

        return cleaned_data

    def save(self, commit=True):
        self.instance.brand = self.cleaned_data.get("brand", "")
        self.instance.model = self.cleaned_data.get("model", "")
        self.instance.series = self.cleaned_data.get("series", "")
        self.instance.engine = self.cleaned_data.get("engine", "")
        self.instance.engine_hp = self.cleaned_data.get("engine_hp")
        self.instance.engine_displacement = self.cleaned_data.get("engine_displacement") or ""
        self.instance.vehicle_extras = self.cleaned_data.get("vehicle_extras") or []
        return super().save(commit=commit)
