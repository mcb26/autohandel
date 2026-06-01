from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0007_carlead_technical_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="carlead",
            name="vehicle_color",
            field=models.CharField(
                blank=True,
                choices=[
                    ("schwarz", "Schwarz"),
                    ("weiss", "Weiß"),
                    ("silber", "Silber"),
                    ("grau", "Grau"),
                    ("blau", "Blau"),
                    ("rot", "Rot"),
                    ("gruen", "Grün"),
                    ("braun", "Braun / Beige"),
                    ("gelb", "Gelb / Orange"),
                    ("gold", "Gold / Bronze"),
                    ("violett", "Violett"),
                    ("other", "Sonstige"),
                ],
                default="",
                max_length=30,
            ),
        ),
    ]
