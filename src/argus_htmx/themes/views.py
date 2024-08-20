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

from argus_htmx.themes.utils import get_theme_names

LOG = logging.getLogger(__name__)
THEMES_MODULE = 'argus_htmx'


class ThemeListView(ListView):
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
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
