from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in
from django.core.checks import register
from django.db.models.signals import post_save, pre_save, post_migrate


class FilterConfig(AppConfig):
    name = "argus.filter"
    label = "argus_filter"

    def ready(self):
        # Settings validation
        from .checks import fallback_filter_check

        register(fallback_filter_check)
