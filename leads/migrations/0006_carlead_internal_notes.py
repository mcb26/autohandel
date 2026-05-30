from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0005_carlead_series_engine"),
    ]

    operations = [
        migrations.AddField(
            model_name="carlead",
            name="internal_notes",
            field=models.TextField(blank=True, default=""),
        ),
    ]
