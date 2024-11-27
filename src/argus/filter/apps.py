from django.apps import AppConfig
from django.core.checks import register


class FilterConfig(AppConfig):
    name = "argus.filter"
    label = "argus_filter"

    def ready(self):
        # Settings validation
        from .checks import fallback_filter_check

        register(fallback_filter_check)
