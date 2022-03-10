from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in
from django.core.checks import register
from django.db.models.signals import post_save, pre_save
from django.db.utils import ProgrammingError
from rest_framework.exceptions import APIException


def sync_media():
    from .media import MEDIA_CLASSES, MEDIA_CLASSES_DICT

    try:
        from .models import Media
    except ImportError:
        return

    try:
        for medium in Media.objects.all():
            if not medium.slug in MEDIA_CLASSES_DICT.keys():
                raise APIException("".join([medium.name, " plugin is not registered in MEDIA_PLUGINS"]))
    except ProgrammingError:
        return

    # Check if all media plugins are also saved in Media
    new_media = [
        Media(slug=media_class.MEDIA_SLUG, name=media_class.MEDIA_NAME)
        for media_class in MEDIA_CLASSES
        if not Media.objects.filter(slug=media_class.MEDIA_SLUG)
    ]
    if new_media:
        Media.objects.bulk_create(new_media)


class NotificationprofileConfig(AppConfig):
    name = "argus.notificationprofile"
    label = "argus_notificationprofile"

    def ready(self):
        # Signals
        from .signals import (
            create_default_timeslot,
            sync_email_destination,
        )

        post_save.connect(create_default_timeslot, "argus_auth.User")
        post_save.connect(sync_email_destination, "argus_auth.User")

        # Settings validation
        from .checks import fallback_filter_check

        register(fallback_filter_check)

        # Check if all media in Media has a respective class
        sync_media()
