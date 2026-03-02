import logging
from collections.abc import Sequence
from pathlib import Path
from re import findall

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.staticfiles.finders import find

from argus.htmx import defaults as fallbacks


__all__ = [
    "clean_themes",
    "get_raw_themes_setting",
    "get_theme_names",
    "get_theme_names_from_setting",
    "get_theme_default",
]

ThemesList = list[str | dict[str, dict]]

LOG = logging.getLogger(__name__)


def get_raw_themes_setting():
    return getattr(settings, "DAISYUI_THEMES", fallbacks.DAISYUI_THEMES)


def clean_themes(themes: Sequence[str | dict]) -> ThemesList:
    """Validate a raw themes list and return a cleaned version.

    - Valid string entries pass through
    - Valid dict entries (single-key with dict value) pass through
    - Multi-key dicts are split into individual single-key dicts
    - Invalid entries are skipped with a warning
    """
    cleaned: ThemesList = []
    for entry in themes:
        if isinstance(entry, str):
            if not entry:
                LOG.warning("Skipping empty string theme entry")
                continue
            cleaned.append(entry)
        elif isinstance(entry, dict):
            if not entry:
                LOG.warning("Skipping empty dict theme entry")
                continue
            cleaned.extend(_validated_dict_themes(entry))
        else:
            LOG.warning("Skipping invalid theme entry of type %s: %r", type(entry).__name__, entry)
    return cleaned


def _validated_dict_themes(entry):
    """Yield valid single-key theme dicts from a dict entry."""
    for key, value in entry.items():
        if not isinstance(key, str) or not key:
            LOG.warning("Skipping theme dict entry with invalid key: %r", key)
            continue
        if not isinstance(value, dict):
            LOG.warning("Skipping theme %r: value must be a dict, got %s", key, type(value).__name__)
            continue
        if not value:
            LOG.warning("Theme %r has empty colors dict; daisyUI will use defaults", key)
        yield {key: value}


def get_theme_names_from_setting():
    themes_setting = clean_themes(get_raw_themes_setting())
    theme_names = []
    for theme in themes_setting:
        if isinstance(theme, str):
            theme_names.append(theme)
        elif isinstance(theme, dict):
            theme_names.extend(theme.keys())
    return theme_names


def get_stylesheet_path():
    return getattr(settings, "STYLESHEET_PATH", fallbacks.STYLESHEET_PATH)


def get_theme_names_from_css():
    THEME_NAME_RE = r'"?(?P<theme>[-_\w]+)"?'
    DATA_THEME_RE = rf"\[data-theme={THEME_NAME_RE}\]"

    stylesheet = find(get_stylesheet_path())
    if stylesheet is None:
        LOG.warning("Stylesheet %s not found, cannot extract themes from CSS", get_stylesheet_path())
        return []
    styles_css = Path(stylesheet).read_text()

    return findall(DATA_THEME_RE, styles_css)


def get_theme_names(quiet=True):
    ERROR_MSG = "Themes in settings are out of sync with themes installed"

    theme_names_from_setting = set(get_theme_names_from_setting())
    theme_names_from_css = set(get_theme_names_from_css())
    installed_themes = theme_names_from_setting & theme_names_from_css

    if theme_names_from_setting != installed_themes:
        LOG.warning(ERROR_MSG)
        if not quiet:
            raise ImproperlyConfigured(ERROR_MSG)

    return installed_themes


def get_theme_default():
    return getattr(settings, "THEME_DEFAULT", fallbacks.THEME_DEFAULT)
