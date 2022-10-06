import logging.config

from dotenv import load_dotenv

load_dotenv()

from .base import *


DEBUG = get_bool_env("DEBUG", True)
TEMPLATES[0]["OPTIONS"]["debug"] = get_bool_env("TEMPLATE_DEBUG", True)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_str_env("SECRET_KEY", "secret-secret!")
STATIC_URL = get_str_env("STATIC_URL", "/static/")
STATIC_ROOT = get_str_env("STATIC_ROOT", "static/")
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


INSTALLED_APPS += ["django_extensions"]

# Prints sent emails to the console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = get_str_env("EMAIL_HOST", "localhost")
EMAIL_HOST_USER = get_str_env("EMAIL_HOST_USER")
EMAIL_PORT = get_int_env("EMAIL_PORT", 587)
EMAIL_USE_TLS = True
EMAIL_HOST_PASSWORD = get_str_env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = get_str_env("DEFAULT_FROM_EMAIL", "argus@localhost")

SEND_NOTIFICATIONS = get_bool_env("ARGUS_SEND_NOTIFICATIONS", default=False)

# Paths to plugins
MEDIA_PLUGINS = [
    "argus.notificationprofile.media.email.EmailNotification",
    "argus.notificationprofile.media.sms_as_email.SMSNotification",
]

# PSA for login

SOCIAL_AUTH_DATAPORTEN_KEY = get_str_env("ARGUS_DATAPORTEN_KEY")
SOCIAL_AUTH_DATAPORTEN_SECRET = get_str_env("ARGUS_DATAPORTEN_SECRET")

SOCIAL_AUTH_DATAPORTEN_EMAIL_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_EMAIL_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET

SOCIAL_AUTH_DATAPORTEN_FEIDE_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_FEIDE_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET

## Logging setup

LOGGING_CONFIG = None
if not LOGGING_MODULE:
    LOGGING_MODULE = "argus.site.logging.DEV"
    DEV_LOGGING = setup_logging(LOGGING_MODULE)
