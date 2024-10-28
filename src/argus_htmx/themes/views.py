import logging

from django.contrib import messages
from django.shortcuts import render
from django.views.generic import ListView

from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse, HttpResponseRedirect
from django_htmx.http import HttpResponseClientRefresh

from argus_htmx.themes.utils import get_theme_names
from argus_htmx.incidents.views import HtmxHttpRequest

LOG = logging.getLogger(__name__)
THEMES_MODULE = "argus_htmx"


class ThemeListView(ListView):
    http_method_names = ["get", "post", "head", "options", "trace"]
    template_name = "htmx/themes/themes_list.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.themes = sorted(get_theme_names())

    def get_queryset(self):
        return self.themes

    def post(self, request, *args, **kwargs):
        theme = request.POST.get("theme")
        if theme in self.themes:
            request.session["theme"] = theme
            messages.success(request, f'Switched theme to "{theme}"')
        else:
            messages.warning(request, f'Failed to switch to theme "{theme}", no such theme installed')
        return HttpResponseRedirect("")


@require_GET
def theme_names(request: HtmxHttpRequest) -> HttpResponse:
    themes = sorted(get_theme_names())
    return render(request, "htmx/themes/theme_list.html", {"theme_list": themes})


@require_POST
def change_theme(request: HtmxHttpRequest) -> HttpResponse:
    themes = get_theme_names()
    theme = request.POST.get("theme")
    if theme in themes:
        request.session["theme"] = theme
        messages.success(request, f'Switched theme to "{theme}"')
        return HttpResponse(f"{theme}")
    return HttpResponseClientRefresh()
