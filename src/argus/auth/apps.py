from django.apps import AppConfig


class AuthConfig(AppConfig):
    name = "argus.auth"
    label = "argus_auth"

    def ready(self):
        from . import signals  # noqa
