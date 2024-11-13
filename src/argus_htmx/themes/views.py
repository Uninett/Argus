import logging

from django.shortcuts import render

from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse
from django_htmx.http import HttpResponseClientRefresh

from argus.auth.utils import get_preference, save_preference

from argus_htmx.constants import THEME_NAMES
from argus_htmx.incidents.views import HtmxHttpRequest

LOG = logging.getLogger(__name__)
THEMES_MODULE = "argus_htmx"


@require_GET
def theme_names(request: HtmxHttpRequest) -> HttpResponse:
    themes = THEME_NAMES
    return render(request, "htmx/themes/_theme_list.html", {"theme_list": themes})


@require_POST
def change_theme(request: HtmxHttpRequest) -> HttpResponse:
    theme = get_preference(request, "argus_htmx", "theme")
    success = save_preference(request, request.POST, "argus_htmx", "theme")
    if success:
        theme = get_preference(request, "argus_htmx", "theme")
        return HttpResponse(theme)
    return HttpResponseClientRefresh()
