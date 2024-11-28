import logging
from pathlib import Path
from re import findall

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles.finders import find

from argus.htmx import defaults as fallbacks


__all__ = [
    "get_raw_themes_setting",
    "get_theme_names",
    "get_theme_default",
]


LOG = logging.getLogger(__name__)


def get_raw_themes_setting():
    return getattr(settings, "DAISYUI_THEMES", fallbacks.DAISYUI_THEMES)


def get_themes_from_setting():
    themes_setting = get_raw_themes_setting()
    theme_names = []
    for theme in themes_setting:
        if isinstance(theme, str):
            theme_names.append(theme)
        elif isinstance(theme, dict):
            theme_names.extend(theme.keys())
    return theme_names


def get_stylesheet_path():
    return getattr(settings, "STYLESHEET_PATH", fallbacks.STYLESHEET_PATH)


def get_themes_from_css():
    THEME_NAME_RE = r"(?P<theme>[-_\w]+)"
    DATA_THEME_RE = rf"\[data-theme={THEME_NAME_RE}\]"

    absolute_stylesheet_path = Path(find(get_stylesheet_path()))
    styles_css = absolute_stylesheet_path.read_text()

    return findall(DATA_THEME_RE, styles_css)


def get_theme_names(quiet=True):
    ERROR_MSG = "Themes in settings are out of sync with themes installed"

    themes_from_setting = set(get_themes_from_setting())
    themes_from_css = set(get_themes_from_css())
    installed_themes = themes_from_setting & themes_from_css

    all_themes = themes_from_setting | themes_from_css
    if all_themes != installed_themes:
        LOG.warning(ERROR_MSG)
        if not quiet:
            raise ImproperlyConfigured(ERROR_MSG)

    return installed_themes


def get_theme_default():
    return getattr(settings, "THEME_DEFAULT", fallbacks.THEME_DEFAULT)
