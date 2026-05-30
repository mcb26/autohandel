from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0004_carlead_archived"),
    ]

    operations = [
        migrations.AddField(
            model_name="carlead",
            name="series",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="carlead",
            name="engine",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
