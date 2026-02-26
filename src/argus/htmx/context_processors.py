"""
How to use:

Append the "context_processors" list for the TEMPLATES-backend
``django.template.backends.django.DjangoTemplates`` with the full dotted path.

See django settings for ``TEMPLATES``.
"""

from django.conf import settings
from packaging.version import InvalidVersion, Version

from . import defaults
from argus.site.views import get_version


def static_paths(request):
    return {
        "stylesheet_path": getattr(settings, "STYLESHEET_PATH", defaults.STYLESHEET_PATH),
        "htmx_path": getattr(settings, "HTMX_PATH", defaults.HTMX_PATH),
        "hyperscript_path": getattr(settings, "HYPERSCRIPT_PATH", defaults.HYPERSCRIPT_PATH),
        "choices_path": getattr(settings, "CHOICES_PATH", defaults.CHOICES_PATH),
        "flatpickr_js_path": getattr(settings, "FLATPICKR_JS_PATH", defaults.FLATPICKR_JS_PATH),
        "flatpickr_css_path": getattr(settings, "FLATPICKR_CSS_PATH", defaults.FLATPICKR_CSS_PATH),
    }


def banner_message(request):
    return {"banner_message": getattr(settings, "BANNER_MESSAGE", None)}


def metadata(request):
    full_version = get_version()
    try:
        short_version = str(Version(full_version).base_version)
    except (InvalidVersion, TypeError):
        short_version = full_version or ""
    return {"version": full_version, "short_version": short_version}
