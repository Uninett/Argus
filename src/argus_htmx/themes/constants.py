from argus_htmx.themes.utils import get_theme_names


__all__ = [
    "THEME_CHOICES",
    "THEME_NAMES",
]


THEME_NAMES = sorted(get_theme_names())
THEME_CHOICES = tuple((theme, theme) for theme in THEME_NAMES)
