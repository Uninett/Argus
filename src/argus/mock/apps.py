from django.apps import AppConfig


class MockConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    label = "guest_mock"
    name = "argus.mock"
