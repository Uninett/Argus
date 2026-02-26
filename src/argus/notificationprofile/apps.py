from django.apps import AppConfig
from django.db.models.signals import post_save, post_migrate


class NotificationprofileConfig(AppConfig):
    name = "argus.notificationprofile"
    label = "argus_notificationprofile"

    def ready(self):
        # Signals
        from .signals import (
            create_default_timeslot,
            sync_email_destination,
            sync_media,
            task_send_notification,  # noqa
            task_background_send_notification,
        )

        post_save.connect(create_default_timeslot, "argus_auth.User")
        post_save.connect(sync_email_destination, "argus_auth.User")
        post_migrate.connect(sync_media, sender=self)

        # sending notifications
        post_save.connect(task_background_send_notification, "argus_incident.Event", dispatch_uid="send_notification")
