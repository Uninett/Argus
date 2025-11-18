import logging
from importlib.metadata import version, PackageNotFoundError

from django.conf import settings
from django.http import (
    Http404,
    HttpResponseBadRequest,
)
from django.shortcuts import render, reverse
from django.views.decorators.http import require_GET
from django.utils.html import escape

from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import status as drf_status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .serializers import MetadataSerializer

LOG = logging.getLogger(__name__)


# fmt: off
def index(request):
    context = {
        "page_title": "Home",
        "frontend": settings.FRONTEND_URL,
    }
    return render(request, "index.html", context=context)
index.login_required = False
# fmt: on


# fmt: off
@api_view(["GET", "HEAD", "POST"])
@permission_classes([permissions.AllowAny])
def api_gone(request, message: str = "Gone"):
    data = {
        "status_code": drf_status.HTTP_410_GONE,
        "status": message,
    }
    return Response(data, status=drf_status.HTTP_410_GONE)
api_gone.login_required = False
# fmt: on


# fmt: off
@require_GET
def error(request):
    error_codes = [400, 401, 403, 404, 410, 500]
    errors = ", ".join(map(str, error_codes))
    status_code = (request.GET.get("status-code", None))
    if status_code is None:
        errormsg = "No status code provided"
        LOG.error(errormsg)
        return HttpResponseBadRequest(errormsg)

    if str(status_code).isdigit():
        status_code = int(status_code)

    if status_code not in error_codes:
        errormsg = f'Status code {escape(status_code)} not in {errors}'
        LOG.error(f"{status_code} {errormsg}")
        return HttpResponseBadRequest(errormsg)

    errormsg = f'This is a test {status_code} error, please ignore'
    LOG.error(f"{status_code} {errormsg}")
    if status_code == 404:
        raise Http404(errormsg)
    elif status_code == 500:
        raise Exception(errormsg)
    else:
        return render(request, f'{status_code}.html', status=status_code)
# fmt: on


def get_version():
    try:
        from argus.version import __version__

        return __version__
    except (ModuleNotFoundError, ImportError):
        pass
    try:
        return version("argus-server")
    except PackageNotFoundError as e:
        return str(e)
    return "version not found"


@extend_schema_view(get=extend_schema(responses=MetadataSerializer))
class MetadataView(APIView):
    http_method_names = ["get", "head", "options", "trace"]
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    login_required = False

    def get(self, request, format=None):
        metadata = {
            "server-version": get_version(),
            "api-version": {
                "stable": "v2",
            },
            "jsonapi-schema": {
                "stable": reverse("schema-v2"),
                "v2": "/api/v2/schema/",
            },
            "ticket_plugin": getattr(settings, "TICKET_PLUGIN", None),
            "destination_plugins": getattr(settings, "MEDIA_PLUGINS", None),
        }
        return Response(metadata)
