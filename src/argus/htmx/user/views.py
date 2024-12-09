from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django_htmx.http import HttpResponseClientRefresh

from argus.auth.utils import save_preferences, save_preference

from argus.htmx.incidents.views import HtmxHttpRequest


@require_GET
def user_preferences(request) -> HttpResponse:
    """Renders the main preferences page for a user"""
    context = {
        "page_title": "User preferences",
    }
    return render(request, "htmx/user/preferences.html", context=context)


@require_POST
def update_preferences(request: HtmxHttpRequest, namespace: str) -> HttpResponse:
    save_preferences(request, request.POST, namespace)
    return HttpResponseClientRefresh()


@require_POST
def update_theme(request: HtmxHttpRequest) -> HttpResponse:
    """Special case for theme since it does not require a full page refresh"""
    success = save_preference(request, request.POST, "argus_htmx", "theme")
    if success:
        return render(request, "htmx/user/_current_theme.html")
    return HttpResponseClientRefresh()
