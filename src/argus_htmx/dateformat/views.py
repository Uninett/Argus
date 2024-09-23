import logging

from django.contrib import messages
from django.shortcuts import render

from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse
from django_htmx.http import HttpResponseClientRefresh

from argus_htmx.incidents.views import HtmxHttpRequest
from .constants import DATETIME_DEFAULT, DATETIME_FORMATS

LOG = logging.getLogger(__name__)


@require_GET
def dateformat_names(request: HtmxHttpRequest) -> HttpResponse:
    datetime_formats = DATETIME_FORMATS.keys()
    return render(request, "htmx/dateformat/_dateformat_list.html", {"datetime_formats": datetime_formats})


@require_POST
def change_dateformat(request: HtmxHttpRequest) -> HttpResponse:
    datetime_format_name = request.POST.get("dateformat", DATETIME_DEFAULT)
    default_format = DATETIME_FORMATS[DATETIME_DEFAULT]
    datetime_format = DATETIME_FORMATS.get(datetime_format_name, default_format)
    request.session["datetime_format"] = datetime_format
    request.session["datetime_format_name"] = datetime_format_name
    messages.success(request, f'Switched dateformat to "{datetime_format_name}"')
    return HttpResponseClientRefresh()
