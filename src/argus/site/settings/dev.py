import logging.config

from dotenv import load_dotenv

load_dotenv()

from .base import *
from argus.spa.settings import *


DEBUG = get_bool_env("DEBUG", True)
TEMPLATES[0]["OPTIONS"]["debug"] = get_bool_env("TEMPLATE_DEBUG", True)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_str_env("SECRET_KEY", "secret-secret!")
STATIC_ROOT = get_str_env("STATIC_ROOT", "staticfiles/")


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


INSTALLED_APPS += ["django_extensions"]

# Paths to plugins
MEDIA_PLUGINS = [
    "argus.notificationprofile.media.email.EmailNotification",
    "argus.notificationprofile.media.sms_as_email.SMSNotification",
]

## Logging setup

LOGGING_CONFIG = None
if not LOGGING_MODULE:
    LOGGING_MODULE = "argus.site.logging.DEV"
    DEV_LOGGING = setup_logging(LOGGING_MODULE)
