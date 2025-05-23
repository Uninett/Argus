"""
How to use:

Append the "context_processors" list for the TEMPLATES-backend
``django.template.backends.django.DjangoTemplates`` with the full dotted path.

See django settings for ``TEMPLATES``.
"""

from django.conf import settings

from . import defaults


def static_paths(request):
    return {
        "stylesheet_path": getattr(settings, "STYLESHEET_PATH", defaults.STYLESHEET_PATH),
        "htmx_path": getattr(settings, "HTMX_PATH", defaults.HTMX_PATH),
        "hyperscript_path": getattr(settings, "HYPERSCRIPT_PATH", defaults.HYPERSCRIPT_PATH),
    }


def banner_message(request):
    return {"banner_message": getattr(settings, "BANNER_MESSAGE", None)}
