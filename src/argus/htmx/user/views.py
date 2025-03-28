from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django_htmx.http import HttpResponseClientRefresh

from argus.auth.utils import get_preference_obj, save_preferences
from argus.htmx.incident.views import HtmxHttpRequest


@require_GET
def user_preferences(request) -> HttpResponse:
    """Renders the main preferences page for a user"""
    context = {
        "page_title": "User preferences",
    }
    return render(request, "htmx/user/preferences.html", context=context)


@require_POST
def update_preferences(request: HtmxHttpRequest, namespace: str) -> HttpResponse:
    try:
        prefs = get_preference_obj(request, namespace)
    except ValueError:
        raise Http404(f"Invalid namespace '{namespace}'")

    saved, failed = save_preferences(request, request.POST, prefs)

    if not request.htmx:
        # We're only expecting htmx requests, but let's make sure to behave decently in case of a regular request
        return HttpResponseRedirect(request.META.HTTP_REFERER or settings.LOGIN_REDIRECT_URL)

    # special case if we're only updating a single preference that has a partial template
    # defined
    if len(saved) == 1 and not failed and (template := prefs.FIELDS[saved[0]].partial_response_template) is not None:
        return render(request, template)

    return HttpResponseClientRefresh()
