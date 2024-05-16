import importlib_resources
import logging
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, reverse, get_object_or_404
from django.views.generic import ListView

from django.views.decorators.http import require_GET
from django.http import HttpResponseRedirect


LOG = logging.getLogger(__name__)
THEMES_MODULE = 'argus_htmx'
THEMES_PATH = "static/themes/"


def get_theme_files(request):
    theme_files_dir = importlib_resources.files(THEMES_MODULE).joinpath(THEMES_PATH)
    absolute_filenames = (path for path in theme_files_dir.iterdir())
    theme_names = []
    for f in absolute_filenames:
        if not f.suffix == '.css':
            continue
        filename = f.name.rstrip('.css')
        theme_names.append(filename)
    return sorted(theme_names)


class ThemeListView(ListView):
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    template_name = "htmx/themes/themes_list.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.themes = get_theme_files(request)

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
