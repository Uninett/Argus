"""
How to use:

Append the "context_processors" list for the TEMPLATES-backend
``django.template.backends.django.DjangoTemplates`` with the full dotted path.

See django settings for ``TEMPLATES``.
"""

from django.conf import settings

from argus.htmx.constants import ALLOWED_PAGE_SIZES, DATETIME_FORMATS, THEME_NAMES
from . import defaults


def path_to_stylesheet(request):
    return {"path_to_stylesheet": getattr(settings, "STYLESHEET_PATH", defaults.STYLESHEET_PATH)}


def preference_options(request):
    # TODO: generalize through Preferences object in argus.auth.context_processors.preferences
    return {
        "preference_options": {
            "datetime_formats": DATETIME_FORMATS.keys(),
            "theme_list": THEME_NAMES,
            "page_sizes": sorted(ALLOWED_PAGE_SIZES),
        },
    }
