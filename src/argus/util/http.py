from http import HTTPStatus
from django.http import HttpResponse


class HttpResponseNoContent(HttpResponse):
    status_code = HTTPStatus.NO_CONTENT
