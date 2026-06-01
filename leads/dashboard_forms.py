from django import forms

from .document_templates import validate_docx_upload
from .models import DealerDocumentTemplate


class DealerTemplateUploadForm(forms.Form):
    file = forms.FileField(
        label="Word-Vorlage (.docx)",
        help_text="Platzhalter wie {{ kunde_name }} oder {{ fahrzeug }} verwenden.",
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        validate_docx_upload(uploaded)
        return uploaded


def save_dealer_template(template_type: str, uploaded_file, user) -> DealerDocumentTemplate:
    existing = DealerDocumentTemplate.objects.filter(template_type=template_type).first()
    if existing and existing.file:
        existing.file.delete(save=False)

    obj, _created = DealerDocumentTemplate.objects.update_or_create(
        template_type=template_type,
        defaults={
            "file": uploaded_file,
            "original_filename": uploaded_file.name,
            "uploaded_by": user if user.is_authenticated else None,
        },
    )
    return obj
