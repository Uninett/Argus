from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_save, post_migrate


class NotificationprofileConfig(AppConfig):
    name = "argus.notificationprofile"
    label = "argus_notificationprofile"

    def ready(self):
        # Signals
        from .signals import (
            create_default_timeslot,
            sync_email_destination,
            sync_media,
        )

        post_save.connect(create_default_timeslot, "argus_auth.User")
        post_save.connect(sync_email_destination, "argus_auth.User")
        post_migrate.connect(sync_media, sender=self)
