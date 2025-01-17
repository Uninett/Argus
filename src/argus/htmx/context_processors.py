"""
How to use:

Append the "context_processors" list for the TEMPLATES-backend
``django.template.backends.django.DjangoTemplates`` with the full dotted path.

See django settings for ``TEMPLATES``.
"""

from django.conf import settings

from . import defaults


def path_to_stylesheet(request):
    return {"path_to_stylesheet": getattr(settings, "STYLESHEET_PATH", defaults.STYLESHEET_PATH)}
