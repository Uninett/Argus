"""
How to use:

Append the "context_processors" list for the TEMPLATES-backend
``django.template.backends.django.DjangoTemplates`` with the full dotted path.

See django settings for ``TEMPLATES``.
"""

from argus.auth.models import Preferences


def preferences(request):
    # Try stored preferences first
    if request.user.is_authenticated:
        return {"preferences": request.user.get_preferences_context()}

    # Use defaults if available
    prefdict = Preferences.objects.get_all_defaults()

    # Override with session
    if "preferences" in request.session:
        for namespace, values in request.session["preferences"].items():
            prefdict[namespace].update(values)

    return {"preferences": prefdict}
