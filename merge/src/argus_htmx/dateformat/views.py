import logging

from django.shortcuts import render

from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse
from django_htmx.http import HttpResponseClientRefresh

from argus.auth.utils import save_preference

from argus_htmx.incidents.views import HtmxHttpRequest
from .constants import DATETIME_FORMATS

LOG = logging.getLogger(__name__)


@require_GET
def dateformat_names(request: HtmxHttpRequest) -> HttpResponse:
    datetime_formats = DATETIME_FORMATS.keys()
    return render(request, "htmx/dateformat/_dateformat_list.html", {"datetime_formats": datetime_formats})


@require_POST
def change_dateformat(request: HtmxHttpRequest) -> HttpResponse:
    save_preference(request, request.POST, "argus_htmx", "datetime_format_name")
    return HttpResponseClientRefresh()
