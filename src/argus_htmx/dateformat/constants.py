from django.conf import settings

__all__ = [
    "DATETIME_FALLBACK",
    "DATETIME_FORMATS",
    "DATETIME_DEFAULT",
    "DATETIME_CHOICES",
]


DATETIME_FALLBACK = "LOCALE"
DATETIME_FORMATS = {
    "LOCALE": "DATETIME_FORMAT",  # default
    "ISO": "Y-m-d H:i:s",
    "RFC5322": "r",
    "EPOCH": "U",
}
DATETIME_CHOICES = tuple((format, format) for format in DATETIME_FORMATS)

_datetime_setting = getattr(settings, "ARGUS_FRONTEND_DATETIME_FORMAT", DATETIME_FALLBACK)

DATETIME_DEFAULT = DATETIME_FALLBACK
if _datetime_setting in DATETIME_FORMATS:
    DATETIME_DEFAULT = _datetime_setting
