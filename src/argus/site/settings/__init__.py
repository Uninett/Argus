from __future__ import annotations

import json
from os import getenv
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from ._serializers import ListAppSetting
from argus.logging.utils import setup_logging


__all__ = [
    "SETTINGS_DIR",
    "SITE_DIR",
    "BASE_DIR",
    "get_bool_env",
    "get_str_env",
    "get_int_env",
    "get_json_env",
    "validate_app_setting",
    "setup_logging",
    "update_loglevels",
    "normalize_url",
]


# Build paths inside the project like this: BASE_DIR / ...
SETTINGS_DIR = Path(__file__).resolve().parent
SITE_DIR = SETTINGS_DIR.parent
BASE_DIR = SITE_DIR.parent


# deserialize environment variables. There are libraries to do this,
# but we haven't settled on one (they tend to be bloated)


def get_any_env(envname, required=False):
    env = getenv(envname)
    if env is None:
        # Envvar not set!
        if required:
            error = f'Environment variable "{envname}" not set!'
            raise OSError(error)
        return None
    return env


def get_bool_env(envname, default=None, required=False):
    env = get_any_env(envname, required)
    env = str(env).lower()
    if env in {"1", "on", "true", "yes"}:
        return True
    if env in {"0", "off", "false", "no"}:
        return False
    return default


def get_str_env(envname, default="", required=False):
    env = get_any_env(envname, required)
    if env is None:
        return default
    return str(env).strip()


def get_int_env(envname, default=0, required=False):
    env = get_any_env(envname, required)
    if env is None:
        return default
    env = str(env).strip()
    return int(env)


def get_json_env(envname, default=None, required=False, quiet=True):
    if default is None:
        default = {}
    env = get_any_env(envname, required)
    if env is None:
        return default
    try:
        return json.loads(env)
    except json.JSONDecodeError as e:
        if quiet:
            return default
        raise AttributeError(e) from e


def validate_app_setting(jsonblob):
    if not jsonblob:
        return []
    app_setting = ListAppSetting.model_validate(jsonblob)
    return app_setting.root


# fixes


def _add_missing_scheme_to_url(url):
    parsed_url = urlsplit(url)
    scheme, netloc, *_ = parsed_url
    if scheme:  # nothing to fix
        return url
    if not netloc:  # relative url
        return url
    port = parsed_url.port
    if port == 80:
        scheme = "http"
    elif port == 443:
        scheme = "https"
    else:
        return url  # nothing to guess
    fixed_url = parsed_url._replace(scheme=scheme)
    return urlunsplit(fixed_url)


def normalize_url(url):
    scheme_url = _add_missing_scheme_to_url(url)
    parsed_url = urlsplit(scheme_url)
    scheme, netloc, *_ = parsed_url
    port = parsed_url.port
    if scheme not in ("http", "https"):
        # nothing to normalize
        return url
    if port is None or port not in (80, 443):
        # nothing to normalize
        return url
    netloc = "".join(netloc.rsplit(":", 1)[0])
    fixed_url = parsed_url._replace(netloc=netloc)
    return urlunsplit(fixed_url)
