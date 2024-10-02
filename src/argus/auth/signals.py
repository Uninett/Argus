from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, Preferences


@receiver(post_save, sender=User)
def ensure_preferences(sender, instance, created, **kwargs):
    Preferences.objects.get_or_create(user=instance)
