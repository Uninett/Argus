import logging

from django.shortcuts import render
from django.views.generic import ListView

from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse, HttpResponseRedirect
from django_htmx.http import HttpResponseClientRefresh

from argus.auth.utils import get_preference, save_preference

from argus_htmx.constants import THEME_NAMES
from argus_htmx.incidents.views import HtmxHttpRequest

LOG = logging.getLogger(__name__)
THEMES_MODULE = "argus_htmx"


class ThemeListView(ListView):
    http_method_names = ["get", "post", "head", "options", "trace"]
    template_name = "htmx/themes/themes_list.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.themes = THEME_NAMES

    def get_queryset(self):
        return self.themes

    def post(self, request, *args, **kwargs):
        save_preference(request, request.POST, "argus_htmx", "theme")
        return HttpResponseRedirect("")


@require_GET
def theme_names(request: HtmxHttpRequest) -> HttpResponse:
    themes = THEME_NAMES
    return render(request, "htmx/themes/theme_list.html", {"theme_list": themes})


@require_POST
def change_theme(request: HtmxHttpRequest) -> HttpResponse:
    theme = get_preference(request, "argus_htmx", "theme")
    success = save_preference(request, request.POST, "argus_htmx", "theme")
    if success:
        theme = get_preference(request, "argus_htmx", "theme")
        return HttpResponse(theme)
    return HttpResponseClientRefresh()
