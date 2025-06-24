from django.db.models.signals import post_save
from django.dispatch import receiver

from app.models import AdminUser


@receiver([post_save], sender=AdminUser)
def post_save_post(sender, instance, created, **kwargs):
    if created:
        pass
