from django.db import models


class CarLead(models.Model):
    STATUS_NEW = "new"
    STATUS_CONTACTED = "contacted"
    STATUS_REJECTED = "rejected"
    STATUS_BOUGHT = "bought"

    STATUS_CHOICES = [
        (STATUS_NEW, "Neu"),
        (STATUS_CONTACTED, "Kontaktiert"),
        (STATUS_REJECTED, "Abgelehnt"),
        (STATUS_BOUGHT, "Gekauft"),
    ]

    CONDITION_CHOICES = [
        ("sehr_gut", "Sehr gut"),
        ("gut", "Gut"),
        ("gebraucht", "Gebraucht / fahrbereit"),
        ("unfall", "Unfallfahrzeug"),
        ("defekt", "Defekt / Bastlerfahrzeug"),
    ]

    FUEL_TYPE_CHOICES = [
        ("benzin", "Benzin"),
        ("diesel", "Diesel"),
        ("elektro", "Elektro"),
        ("hybrid", "Hybrid"),
        ("gas", "Gas (LPG/CNG)"),
        ("other", "Sonstiges"),
    ]

    COLOR_CHOICES = [
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
    ]

    VEHICLE_FEATURE_FIELDS = (
        ("feature_maintenance", "Wartung"),
        ("feature_roadworthy", "Fahrtauglich"),
        ("feature_warranty", "Garantie"),
        ("feature_inspection_new", "Inspektion neu"),
        ("feature_non_smoker", "Nichtraucher-Fahrzeug"),
        ("feature_service_book", "Scheckheftgepflegt"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(blank=True, null=True)

    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=120)
    series = models.CharField(max_length=200, blank=True, default="")
    engine = models.CharField(max_length=200, blank=True, default="")
    engine_hp = models.PositiveSmallIntegerField(null=True, blank=True)
    engine_displacement = models.CharField(max_length=20, blank=True, default="")
    fuel_type = models.CharField(max_length=30, choices=FUEL_TYPE_CHOICES, blank=True, default="")
    first_registration = models.DateField()
    tuv_until = models.DateField(null=True, blank=True)
    mileage = models.PositiveIntegerField()
    vehicle_color = models.CharField(max_length=30, choices=COLOR_CHOICES, blank=True, default="")
    vehicle_condition = models.CharField(max_length=100, choices=CONDITION_CHOICES)
    expected_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    feature_maintenance = models.BooleanField(default=False)
    feature_roadworthy = models.BooleanField(default=False)
    feature_warranty = models.BooleanField(default=False)
    feature_inspection_new = models.BooleanField(default=False)
    feature_non_smoker = models.BooleanField(default=False)
    feature_service_book = models.BooleanField(default=False)

    vehicle_extras = models.JSONField(default=list, blank=True)

    customer_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    postal_code = models.CharField(max_length=10)
    message = models.TextField(blank=True)
    privacy_accepted = models.BooleanField(default=False)
    marketing_consent = models.BooleanField(default=False, blank=True)

    internal_notes = models.TextField(blank=True, default="")
    source_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Auto-Anfrage"
        verbose_name_plural = "Auto-Anfragen"

    @property
    def first_registration_display(self) -> str:
        """Erstzulassung als MM/JJJJ (nur Ziffern, keine Monatsnamen)."""
        if not self.first_registration:
            return "-"
        return self.first_registration.strftime("%m/%Y")

    @property
    def tuv_until_display(self) -> str:
        if not self.tuv_until:
            return "-"
        return self.tuv_until.strftime("%m/%Y")

    @property
    def engine_technical_summary(self) -> str:
        parts = []
        if self.engine_displacement:
            parts.append(f"{self.engine_displacement} l")
        if self.engine_hp:
            parts.append(f"{self.engine_hp} PS")
        if self.fuel_type:
            parts.append(self.get_fuel_type_display())
        return " · ".join(parts)

    def active_vehicle_features(self) -> list[str]:
        labels = []
        for field_name, label in self.VEHICLE_FEATURE_FIELDS:
            if getattr(self, field_name, False):
                labels.append(label)
        return labels

    def selected_vehicle_extras(self) -> list[str]:
        from .vehicle_extras import VEHICLE_EXTRAS_LABELS

        labels = []
        for key in self.vehicle_extras or []:
            label = VEHICLE_EXTRAS_LABELS.get(key)
            if label:
                labels.append(label)
        return labels

    def vehicle_summary(self) -> str:
        parts = [self.brand, self.model]
        if self.series:
            parts.append(self.series)
        if self.engine:
            parts.append(self.engine)
        return " · ".join(parts)

    def thank_you_summary(self) -> str:
        """Kurzzeile für die Danke-Seite."""
        mileage = f"{self.mileage:,}".replace(",", ".")
        return f"{self.vehicle_summary()} · EZ {self.first_registration_display} · {mileage} km"

    def __str__(self) -> str:
        return f"{self.customer_name} - {self.vehicle_summary()}"


class CarLeadImage(models.Model):
    lead = models.ForeignKey(CarLead, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="lead_images/%Y/%m/%d/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Lead-Bild"
        verbose_name_plural = "Lead-Bilder"

    def __str__(self) -> str:
        return f"Bild zu Lead #{self.lead_id}"
