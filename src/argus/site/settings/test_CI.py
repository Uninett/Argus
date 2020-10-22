import subprocess
import logging.config

from django.utils.log import DEFAULT_LOGGING

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

FRONTEND_URL = get_str_env("ARGUS_FRONTEND_URL")

CORS_ORIGIN_WHITELIST = []
if FRONTEND_URL:
    CORS_ORIGIN_WHITELIST.append(FRONTEND_URL)


# Prints sent emails to the console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = get_str_env("EMAIL_HOST", "localhost")
EMAIL_HOST_USER = get_str_env("EMAIL_HOST_USER")
EMAIL_PORT = get_int_env("EMAIL_PORT", 587)
EMAIL_USE_TLS = True
EMAIL_HOST_PASSWORD = get_str_env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = get_str_env("DEFAULT_FROM_EMAIL", "argus@localhost")

SEND_NOTIFICATIONS = get_bool_env("ARGUS_SEND_NOTIFICATIONS", default=False)

# PSA for login

SOCIAL_AUTH_DATAPORTEN_KEY = get_str_env("ARGUS_DATAPORTEN_KEY")
SOCIAL_AUTH_DATAPORTEN_SECRET = get_str_env("ARGUS_DATAPORTEN_SECRET")

SOCIAL_AUTH_DATAPORTEN_EMAIL_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_EMAIL_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET

SOCIAL_AUTH_DATAPORTEN_FEIDE_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_FEIDE_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET

## Logging setup

_LOGGER = logging.getLogger(__name__)


# Use in-memory channel layer when testing.
# fmt: off
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
# fmt: on


POSTGRES = get_bool_env("POSTGRES")
POSTGRES_DB = get_str_env("POSTGRES_DB")
POSTGRES_USER = get_str_env("POSTGRES_USER")
POSTGRES_PASSWORD = get_str_env("POSTGRES_PASSWORD")

if POSTGRES:
    # fmt: off
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": POSTGRES_DB,
            "USER": POSTGRES_USER,
            "PASSWORD": POSTGRES_PASSWORD,
            "HOST": "localhost",
        }
    }
    # fmt: on
    try:
        postgres_version_str = subprocess.check_output(["pg_config", "--version"]).decode().strip()
    except Exception as e:
        _LOGGER.error(e)
        postgres_version_str = "PostgreSQL (unable to get version)"
    _LOGGER.debug(f"Using {postgres_version_str} as database backend.")
else:
    # fmt: off
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
    # fmt: on
