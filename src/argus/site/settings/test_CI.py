import os
import subprocess
import logging.config

from . import get_bool_env, get_str_env
from .base import *  # noqa: F403
from ..utils import update_settings

from argus.htmx.appconfig import APP_SETTINGS

update_settings(globals(), APP_SETTINGS)
ROOT_URLCONF = "argus.htmx.root_urls"

DEBUG = get_bool_env("DEBUG", True)
TEMPLATES[0]["OPTIONS"]["debug"] = get_bool_env("TEMPLATE_DEBUG", True)  # noqa: F405


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_str_env("SECRET_KEY", "secret-secret!")
STATIC_ROOT = get_str_env("STATIC_ROOT", "staticfiles/")


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

# Paths to plugins
MEDIA_PLUGINS = [
    "argus.notificationprofile.media.email.EmailNotification",
    "argus.notificationprofile.media.sms_as_email.SMSNotification",
]

# Tests

TEST_RUNNER = "xmlrunner.extra.djangotestrunner.XMLTestRunner"
TEST_OUTPUT_VERBOSE = 2
# This ensures that each tox environment receives test reports in separate directories. If not running tests under tox,
# reports land directly in test-reports/
TEST_OUTPUT_DIR = os.path.join("test-reports", os.getenv("TOX_ENV_NAME", ""))
TEST_OUTPUT_FILE_NAME = "test-results.xml"

# Logging setup

_LOGGER = logging.getLogger(__name__)


# Use in-memory channel layer when testing.
# fmt: off
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
# fmt: on

try:
    postgres_version_str = subprocess.check_output(["pg_config", "--version"]).decode().strip()
except Exception as e:
    _LOGGER.error(e)
    postgres_version_str = "PostgreSQL (unable to get version)"
_LOGGER.debug(f"Using {postgres_version_str} as database backend.")
