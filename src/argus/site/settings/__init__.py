from __future__ import annotations

import json
import re
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
    "normalize_suburl",
    "prefix_relative_url",
    "append_suburl",
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


# other helpers


def normalize_suburl(suburl: str) -> str:
    """Normalize a sub-path prefix to the only form ``django.urls.path()`` accepts

    That form has no leading slash and exactly one trailing slash. Both
    "/argus/" and "argus" are natural things to put in an environment
    variable, and both misroute: a route starting with a slash never matches
    anything, while a route without a trailing slash matches greedily, so
    "argus" would serve the incident list at "/argusincidents/". Accept every
    spelling and settle on "argus/".

    An empty suburl means "serve from the domain root" and stays empty.
    """
    suburl = re.sub(r"/+", "/", suburl.strip()).strip("/")
    if not suburl:
        return ""
    return f"{suburl}/"


def prefix_relative_url(urlpath: str, suburl: str = "") -> str:
    """Move a root-relative url path into the sub-site at ``suburl``

    "/api/" becomes "/argus/api/". Absolute-ness is part of the meaning of
    these paths: they are compared against ``request.path`` and handed to
    browsers as redirect targets, so the leading slash is preserved.

    Anything that does not address this site is left alone, which covers both
    the full "https://cdn.example.org/" and the protocol-relative
    "//cdn.example.org/" spelling of a CDN url, as well as genuinely relative
    paths. Prefixing is idempotent.
    """
    suburl = normalize_suburl(suburl)
    if not suburl or not _is_root_relative(urlpath):
        return urlpath

    prefix = f"/{suburl}"
    if urlpath == prefix.rstrip("/"):
        return prefix
    if urlpath.startswith(prefix):
        return urlpath
    return prefix + urlpath.lstrip("/")


def append_suburl(url: str, suburl: str = "") -> str:
    """Move a full url, such as the one permalinks are built from, into ``suburl``

    The result always ends in a slash, which is load-bearing rather than
    cosmetic: these urls are urljoin()ed with relative paths, and urljoin drops
    the last segment of a base that does not end in one. Appending is
    idempotent, and an empty url stays empty.
    """
    suburl = normalize_suburl(suburl)
    if not suburl or not url:
        return url

    tail = f"/{suburl.rstrip('/')}"
    url = url.rstrip("/")
    if not url.endswith(tail):
        url += tail
    return f"{url}/"


def _is_root_relative(urlpath: str) -> bool:
    parsed = urlsplit(urlpath)
    if parsed.scheme or parsed.netloc:
        return False
    return urlpath.startswith("/")


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
