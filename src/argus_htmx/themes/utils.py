from django.conf import settings
from argus_htmx import settings as argus_htmx_settings


def get_themes():
    return getattr(settings, "DAISYUI_THEMES", argus_htmx_settings.DAISYUI_THEMES)


def get_theme_names():
    themes = get_themes()
    theme_names = []
    for theme in themes:
        if isinstance(theme, str):
            theme_names.append(theme)
        elif isinstance(theme, dict):
            theme_names.extend(theme.keys())
    return theme_names
