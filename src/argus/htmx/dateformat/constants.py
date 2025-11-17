import dataclasses
from django.conf import settings

__all__ = [
    "DATETIME_FORMATS",
    "get_datetime_format_default",
]


@dataclasses.dataclass
class DateTimeFormat:
    datetime: str
    date: str
    time: str


DATETIME_FALLBACK = "LOCALE"

# Datetime format specification can be found here:
# https://docs.djangoproject.com/en/5.1/ref/templates/builtins/#date
DATETIME_FORMATS = {
    "LOCALE": DateTimeFormat(datetime="DATETIME_FORMAT", date="DATE_FORMAT", time="TIME_FORMAT"),  # default
    "ISO": DateTimeFormat(datetime="Y-m-d H:i:s", date="Y-m-d", time="H:i:s"),
    "RFC5322": DateTimeFormat("r", "r", "r"),
    "EPOCH": DateTimeFormat("U", "U", "U"),
}


def get_datetime_format_default():
    _datetime_setting = getattr(settings, "ARGUS_FRONTEND_DATETIME_FORMAT", DATETIME_FALLBACK)

    datetime_default = DATETIME_FALLBACK
    if _datetime_setting in DATETIME_FORMATS:
        datetime_default = _datetime_setting
    return datetime_default
