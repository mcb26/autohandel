from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0006_carlead_internal_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="carlead",
            name="engine_hp",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="carlead",
            name="engine_displacement",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="carlead",
            name="fuel_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("benzin", "Benzin"),
                    ("diesel", "Diesel"),
                    ("elektro", "Elektro"),
                    ("hybrid", "Hybrid"),
                    ("gas", "Gas (LPG/CNG)"),
                    ("other", "Sonstiges"),
                ],
                default="",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="carlead",
            name="tuv_until",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="carlead",
            name="feature_maintenance",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="carlead",
            name="feature_roadworthy",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="carlead",
            name="feature_warranty",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="carlead",
            name="feature_inspection_new",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="carlead",
            name="feature_non_smoker",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="carlead",
            name="feature_service_book",
            field=models.BooleanField(default=False),
        ),
    ]
