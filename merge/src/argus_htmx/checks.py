from django.core.checks import Error, Warning, register
from django.core.exceptions import ImproperlyConfigured

from .themes.utils import get_theme_names, get_stylesheet_path


@register
def check_for_valid_themes_list(app_configs, **kwargs):
    styles_path = get_stylesheet_path()
    themes = []
    try:
        themes = get_theme_names(quiet=False)
    except ImproperlyConfigured as e:
        return [
            Warning(
                str(e),
                hint=f"Regenerate {styles_path}",
                id="argus_htmx.T001",
            )
        ]
    if not themes:
        return [
            Error(
                "no themes installed",
                hint=f'Check the settings "DAISYUI_THEMES" and "TAILWIND_THEME_OVERRIDE" and regenerate {styles_path}',
                id="argus_htmx.T002",
            )
        ]
    return []
