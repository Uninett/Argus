from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in
from django.core.checks import register
from django.db.models.signals import post_save, pre_save


class NotificationprofileConfig(AppConfig):
    name = "argus.notificationprofile"
    label = "argus_notificationprofile"

    def ready(self):
        # Signals
        from .signals import (
            add_synced_flag,
            create_default_destination_config,
            create_default_timeslot,
            update_default_destination_config,
        )

        pre_save.connect(add_synced_flag, "argus_notificationprofile.DestinationConfig")
        post_save.connect(create_default_timeslot, "argus_auth.User")
        post_save.connect(create_default_destination_config, "argus_auth.User")
        user_logged_in.connect(update_default_destination_config, "argus_auth.User")

        # Settings validation
        from .checks import fallback_filter_check

        register(fallback_filter_check)
