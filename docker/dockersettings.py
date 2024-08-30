"""Settings for production-like deployments in Docker"""

from argus.site.settings.prod import *

# Allow all hosts to reach backend, since all requests will typically come from
# outside the container:
ALLOWED_HOSTS = ["*"]

# Uncomment to enable both Email and SMS-as-email notification backends,
# leave commented out to keep just the default email backend:
# MEDIA_PLUGINS = [
#    "argus.notificationprofile.media.email.EmailNotification",
#    "argus.notificationprofile.media.sms_as_email.SMSNotification",
# ]
