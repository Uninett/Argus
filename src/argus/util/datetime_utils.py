from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime


INFINITY_REPR = "infinity"
NEGATIVE_INFINITY_REPR = f"-{INFINITY_REPR}"

INFINITY = datetime.max
NEGATIVE_INFINITY = datetime.min

LOCAL_TIMEZONE = timezone.get_default_timezone()


def make_aware(value: datetime):
    if timezone.is_aware(value):
        return value
    # Safest for avoiding OverflowError
    return value.replace(tzinfo=LOCAL_TIMEZONE)


LOCAL_INFINITY = make_aware(INFINITY)
LOCAL_NEGATIVE_INFINITY = make_aware(NEGATIVE_INFINITY)


def make_naive(value: datetime):
    if timezone.is_naive(value):
        return value
    # Safest for avoiding OverflowError
    return value.replace(tzinfo=None)


def get_infinity_repr(value, *, str_repr):
    if not isinstance(value, datetime):
        return None

    value = make_naive(value)
    if value == INFINITY:
        return INFINITY_REPR if str_repr else INFINITY
    elif value == NEGATIVE_INFINITY:
        return NEGATIVE_INFINITY_REPR if str_repr else NEGATIVE_INFINITY
    return None


def get_infinity_time(value):
    if isinstance(value, datetime):
        value = make_naive(value)
        if value in {INFINITY, NEGATIVE_INFINITY}:
            return make_aware(value)
    elif isinstance(value, str):
        return parse_infinity(value)
    return None


def parse_infinity(value: str, *, return_localized=True):
    if value == INFINITY_REPR:
        return LOCAL_INFINITY if return_localized else INFINITY
    elif value == NEGATIVE_INFINITY_REPR:
        return LOCAL_NEGATIVE_INFINITY if return_localized else NEGATIVE_INFINITY
    return None


# Code based on https://github.com/django/django/blob/dd5aa8cb5ffc0a89c4b9b8dee45c1c919d203489/django/db/backends/sqlite3/operations.py#L276-L282
def convert_datetimefield_value(value, connection):
    if value is not None:
        if not isinstance(value, datetime):
            value = parse_datetime(value)
        if settings.USE_TZ and not timezone.is_aware(value):
            value = timezone.make_aware(value, connection.timezone)
    return value
