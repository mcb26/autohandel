from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CarLeadImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="lead_images/%Y/%m/%d/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "lead",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="leads.carlead",
                    ),
                ),
            ],
            options={
                "verbose_name": "Lead-Bild",
                "verbose_name_plural": "Lead-Bilder",
                "ordering": ["created_at"],
            },
        ),
    ]
