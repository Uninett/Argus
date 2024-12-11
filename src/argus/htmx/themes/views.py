import logging

from django.shortcuts import render

from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse
from django_htmx.http import HttpResponseClientRefresh

from argus.auth.utils import get_or_update_preference

from argus.htmx.constants import THEME_NAMES
from argus.htmx.incidents.views import HtmxHttpRequest

LOG = logging.getLogger(__name__)
THEMES_MODULE = "argus.htmx"


@require_GET
def theme_names(request: HtmxHttpRequest) -> HttpResponse:
    themes = THEME_NAMES
    return render(request, "htmx/themes/_theme_list.html", {"theme_list": themes})


@require_POST
def change_theme(request: HtmxHttpRequest) -> HttpResponse:
    _, success = get_or_update_preference(request, request.POST, "argus_htmx", "theme")
    if success:
        return render(request, "htmx/themes/_current_theme.html")
    return HttpResponseClientRefresh()
