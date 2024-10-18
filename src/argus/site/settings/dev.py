import logging.config
import os

from dotenv import load_dotenv

load_dotenv()

from . import get_bool_env, get_str_env  # noqa: E402
from .base import *  # noqa: E402, F403

os.environ.setdefault("ARGUS_SPA_COOKIE_DOMAIN", "localhost")
from argus.spa.spa_settings import *  # noqa: E402, F403

DEBUG = get_bool_env("DEBUG", True)
TEMPLATES[0]["OPTIONS"]["debug"] = get_bool_env("TEMPLATE_DEBUG", True)  # noqa: F405

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_str_env("SECRET_KEY", "secret-secret!")
STATIC_ROOT = get_str_env("STATIC_ROOT", "staticfiles/")


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


INSTALLED_APPS += ["django_extensions"]  # noqa: F405

# Paths to plugins
MEDIA_PLUGINS = [
    "argus.notificationprofile.media.email.EmailNotification",
    "argus.notificationprofile.media.sms_as_email.SMSNotification",
]

# Logging setup

LOGGING_CONFIG = None
if not LOGGING_MODULE:  # noqa: F405
    LOGGING_MODULE = "argus.site.logging.DEV"
    DEV_LOGGING = setup_logging(LOGGING_MODULE)  # noqa: F405
