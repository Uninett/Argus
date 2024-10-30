from django.shortcuts import render

from django.views.decorators.http import require_http_methods
from django.http import HttpResponse


@require_http_methods(["GET"])
def destination_list(request) -> HttpResponse:
    return _render_destination_list(request)


def _render_destination_list(request) -> HttpResponse:
    return render(request, "htmx/destination/destination_list.html")
