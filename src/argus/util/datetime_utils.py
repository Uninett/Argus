# Re-exported from django_psycopg_infinity.utils for backwards compatibility
from django_psycopg_infinity.utils import (  # noqa: F401
    INFINITY,
    INFINITY_REPR,
    NEGATIVE_INFINITY,
    NEGATIVE_INFINITY_REPR,
    convert_datetimefield_value,
    get_infinity_repr,
    get_infinity_time,
    make_aware,
    make_naive,
    parse_infinity,
)

from django.utils import timezone

LOCAL_TIMEZONE = timezone.get_default_timezone()
LOCAL_INFINITY = make_aware(INFINITY)
LOCAL_NEGATIVE_INFINITY = make_aware(NEGATIVE_INFINITY)
