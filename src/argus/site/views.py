import logging

from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseGone,
    HttpResponseNotFound,
    HttpResponseServerError,
)
from django.shortcuts import render, reverse

from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response


ERROR_TEMPLATE = """<html>
<head><title>{code} {reason}</title></head>
<body><h1>{code} {reason}</h1></body>
</html>
"""

LOG = logging.getLogger(__name__)


def index(request):
    return render(request, "base.html")


def error(request):
    def render_error_page(code, reason) -> bytes:
        return ERROR_TEMPLATE.format(code=code, reason=reason).encode("utf-8")

    ERROR_MAP = {
        400: HttpResponseBadRequest,
        403: HttpResponseForbidden,
        404: HttpResponseNotFound,
        410: HttpResponseGone,
        500: HttpResponseServerError,
    }
    pp_errors = ", ".join([str(code) for code in sorted(ERROR_MAP.keys())])
    status_code = request.GET.get("status-code", None)
    if status_code is None:
        errormsg = f'Status code "{status_code}" not in {pp_errors}'
        content = render_error_page(400, errormsg)
        LOG.error(f"{status_code} {errormsg}")
        return HttpResponseBadRequest(content=content, reason=errormsg)
    try:
        status_code = int(status_code)
    except ValueError:
        errormsg = f'Status code "{status_code}" is not an integer'
        content = render_error_page(400, errormsg)
        LOG.error(f"{status_code} {errormsg}")
        return HttpResponseBadRequest(content=content, reason=errormsg)
    if status_code not in ERROR_MAP.keys():
        errormsg = f'Status code "{status_code}" not in {pp_errors}'
        content = render_error_page(400, errormsg)
        LOG.error(f"{status_code} {errormsg}")
        return HttpResponseBadRequest(content=content, reason=errormsg)

    errormsg = f"{status_code} Generated error"
    if status_code == 500:
        try:
            assert False, status_code
        except AssertionError:
            LOG.exception(errormsg)
    else:
        LOG.error(errormsg)
    content = render_error_page(status_code, "Generated error page")
    return ERROR_MAP[status_code](content=content)


class MetadataView(APIView):
    http_method_names = ["get", "head", "options", "trace"]
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        try:
            from argus.version import __version__
        except (ModuleNotFoundError, ImportError):
            import pkg_resources

            __version__ = pkg_resources.get_distribution("argus-server").version

        metadata = {
            "server-version": __version__,
            "api-version": {
                "stable": "v1",
                "unstable": "v2",
            },
            "jsonapi-schema": {
                "stable": reverse("schema-v1-old"),
                "v1": "/api/v1/schema/",
                "v2": "/api/v2/schema/",
            },
        }
        return Response(metadata)
