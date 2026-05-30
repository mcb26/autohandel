from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0002_carleadimage"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="carlead",
            name="fuel_type",
        ),
        migrations.RemoveField(
            model_name="carlead",
            name="transmission",
        ),
        migrations.RemoveField(
            model_name="carlead",
            name="power_hp",
        ),
    ]
