from django.apps import AppConfig
from django.db.models.signals import post_save


class NotificationprofileConfig(AppConfig):
    name = "argus.notificationprofile"
    label = "argus_notificationprofile"

    def ready(self):
        from .signals import create_default_timeslot

        post_save.connect(create_default_timeslot, "argus_auth.User")
