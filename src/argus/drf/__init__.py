from django.core.exceptions import NON_FIELD_ERRORS as DJANGO_NON_FIELD_ERRORS
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.views import api_settings
from rest_framework.views import exception_handler as drf_exception_handler

DRF_NON_FIELD_ERRORS = api_settings.NON_FIELD_ERRORS_KEY


__all__ = ["exception_handler"]


def exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        data = exc.message_dict
        if DJANGO_NON_FIELD_ERRORS in data:
            data[DRF_NON_FIELD_ERRORS] = data.pop(DJANGO_NON_FIELD_ERRORS)

        exc = DRFValidationError(detail=data)

    return drf_exception_handler(exc, context)
