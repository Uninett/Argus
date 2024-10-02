"""
How to use:

Append the "context_processors" list for the TEMPLATES-backend
``django.template.backends.django.DjangoTemplates`` with the full dotted path.

See django settings for ``TEMPLATES``.
"""

from argus.auth.models import Preferences


def preferences(request):
    pref_sets = Preferences.objects.filter(user=request.user)
    prefdict = {}
    for pref_set in pref_sets:
        prefdict[pref_set._namespace] = pref_set.get_context()
    return {"preferences": prefdict}
