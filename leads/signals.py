from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CarLead
from .telegram_notify import send_lead_telegram_notification


@receiver(post_save, sender=CarLead)
def notify_new_lead_via_telegram(sender, instance: CarLead, created: bool, **kwargs):
    if created:
        send_lead_telegram_notification(instance)
