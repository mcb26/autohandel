from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0008_carlead_vehicle_color"),
    ]

    operations = [
        migrations.AddField(
            model_name="carlead",
            name="vehicle_extras",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
