import os

from dotenv import load_dotenv

load_dotenv()

from . import get_bool_env, get_str_env  # noqa: E402
from .base import *  # noqa: E402, F403

os.environ.setdefault("ARGUS_SPA_COOKIE_DOMAIN", "localhost")
from argus.spa.spa_settings import *  # noqa: E402, F403

DEBUG = get_bool_env("DEBUG", True)

# Disable using Redis in Channels and fall back to an InMemoryChannel
# WARNING: This should only ever be used during development/testing and never
# in production. To enforce this it is only ever activated when DEBUG is also set
# fmt: off
ARGUS_DISABLE_REDIS = get_bool_env("ARGUS_DISABLE_REDIS", False)
if ARGUS_DISABLE_REDIS and DEBUG:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
else:
    _REDIS = urlsplit("//" + get_str_env("ARGUS_REDIS_SERVER", "127.0.0.1:6379"))
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [(_REDIS.hostname, _REDIS.port or 6379)],
            },
        },
    }
# fmt: on

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
