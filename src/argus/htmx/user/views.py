from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django_htmx.http import HttpResponseClientRefresh

from argus.auth.utils import get_or_update_preference

from argus.htmx.incidents.views import HtmxHttpRequest


@require_POST
def change_page_size(request: HtmxHttpRequest) -> HttpResponse:
    get_or_update_preference(request, request.POST, "argus_htmx", "page_size")
    return HttpResponseClientRefresh()


@require_GET
def user_preferences(request) -> HttpResponse:
    """Renders the main preferences page for a user"""
    context = {
        "page_title": "User preferences",
    }
    return render(request, "htmx/user/preferences.html", context=context)
