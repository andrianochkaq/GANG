"""Every new user, however they registered, gets a default fridge."""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .services import create_default_fridge


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_fridge_for_new_user(sender, instance, created, raw=False, **kwargs):
    # raw is True while loading fixtures; their fridges come with them.
    if created and not raw:
        create_default_fridge(instance)
