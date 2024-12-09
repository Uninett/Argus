import logging


from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django_htmx.http import HttpResponseClientRefresh

from argus.auth.utils import get_or_update_preference

from argus.htmx.incidents.views import HtmxHttpRequest

LOG = logging.getLogger(__name__)


@require_POST
def change_dateformat(request: HtmxHttpRequest) -> HttpResponse:
    get_or_update_preference(request, request.POST, "argus_htmx", "datetime_format_name")
    return HttpResponseClientRefresh()
