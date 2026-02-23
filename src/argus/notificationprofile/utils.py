from django.conf import settings


def are_notifications_enabled():
    return getattr(settings, "SEND_NOTIFICATIONS", False)
