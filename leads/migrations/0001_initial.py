from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CarLead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "Neu"),
                            ("contacted", "Kontaktiert"),
                            ("rejected", "Abgelehnt"),
                            ("bought", "Gekauft"),
                        ],
                        default="new",
                        max_length=20,
                    ),
                ),
                ("brand", models.CharField(max_length=100)),
                ("model", models.CharField(max_length=120)),
                ("first_registration", models.DateField()),
                ("mileage", models.PositiveIntegerField()),
                (
                    "fuel_type",
                    models.CharField(
                        choices=[
                            ("benzin", "Benzin"),
                            ("diesel", "Diesel"),
                            ("hybrid", "Hybrid"),
                            ("elektro", "Elektro"),
                            ("lpg", "Autogas (LPG)"),
                            ("cng", "Erdgas (CNG)"),
                            ("other", "Sonstiger Kraftstoff"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "transmission",
                    models.CharField(
                        choices=[
                            ("schaltgetriebe", "Schaltgetriebe"),
                            ("automatik", "Automatik"),
                            ("halbautomatik", "Halbautomatik / Doppelkupplung"),
                            ("other", "Sonstiges Getriebe"),
                        ],
                        max_length=50,
                    ),
                ),
                ("power_hp", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "vehicle_condition",
                    models.CharField(
                        choices=[
                            ("sehr_gut", "Sehr gut"),
                            ("gut", "Gut"),
                            ("gebraucht", "Gebraucht / fahrbereit"),
                            ("unfall", "Unfallfahrzeug"),
                            ("defekt", "Defekt / Bastlerfahrzeug"),
                        ],
                        max_length=100,
                    ),
                ),
                ("expected_price", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("customer_name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=30)),
                ("postal_code", models.CharField(max_length=10)),
                ("message", models.TextField(blank=True)),
                ("privacy_accepted", models.BooleanField(default=False)),
                ("marketing_consent", models.BooleanField(blank=True, default=False)),
                ("source_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Auto-Anfrage",
                "verbose_name_plural": "Auto-Anfragen",
                "ordering": ["-created_at"],
            },
        ),
    ]
