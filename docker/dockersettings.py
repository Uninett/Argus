"""Settings for production-like deployments in Docker"""
from argus.site.settings.prod import *

# Allow all hosts to reach backend, since all requests will typically come from
# outside the container:
ALLOWED_HOSTS = ["*"]

# Enable both Email and SMS notification backends
MEDIA_PLUGINS = [
    "argus.notificationprofile.media.email.EmailNotification",
    "argus.notificationprofile.media.sms_as_email.SMSNotification",
]
