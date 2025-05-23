"""
How to use:

Append the "context_processors" list for the TEMPLATES-backend
``django.template.backends.django.DjangoTemplates`` with the full dotted path.

See django settings for ``TEMPLATES``.
"""

from django.urls import reverse

from .views import LogoutModal


def logout_context(request):
    return {
        "logout_modal": LogoutModal(
            endpoint=reverse("htmx:logout"),
            dialog_id="logout-dialog",
        ),
    }
