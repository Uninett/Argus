from django.core.exceptions import ImproperlyConfigured

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_str_env("SECRET_KEY", required=True)
STATIC_ROOT = get_str_env("STATIC_ROOT", required=True)
STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# You must set this: ip-addresses, hostnames and domain names allowed
# ALLOWED_HOSTS = [
#     "127.0.0.1",
#     "localhost",
# ]

if not FRONTEND_URL:
    raise ImproperlyConfigured('"FRONTEND_URL" has not been set in production!')

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_str_env("EMAIL_HOST", required=True)
DEFAULT_FROM_EMAIL = get_str_env("DEFAULT_FROM_EMAIL", required=True)

SEND_NOTIFICATIONS = get_bool_env("ARGUS_SEND_NOTIFICATIONS", default=True)

# Paths to plugins
MEDIA_PLUGINS = [
    "argus.notificationprofile.media.email.EmailNotification",
]
