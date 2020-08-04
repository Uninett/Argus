from .dev import *


_LOGGER = logging.getLogger(__name__)


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
    _LOGGER.debug(f"Using PostgreSQL as database backend.")
