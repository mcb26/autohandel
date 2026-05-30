from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0003_remove_carlead_fuel_transmission_power"),
    ]

    operations = [
        migrations.AddField(
            model_name="carlead",
            name="is_archived",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="carlead",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
