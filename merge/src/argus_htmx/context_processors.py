"""
How to use:

Append the "context_processors" list for the TEMPLATES-backend
``django.template.backends.django.DjangoTemplates`` with the full dotted path.

See django settings for ``TEMPLATES``.
"""

from .settings import STYLESHEET_PATH


def path_to_stylesheet(request):
    return {"path_to_stylesheet": STYLESHEET_PATH}
