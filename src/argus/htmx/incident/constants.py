from django.conf import settings

from argus.htmx.incident.utils import update_interval_string


__all__ = [
    "PAGE_SIZE_DEFAULT",
    "PAGE_SIZE_CHOICES",
    "INCIDENTS_TABLE_LAYOUT_CHOICES",
    "INCIDENTS_TABLE_LAYOUT_DEFAULT",
    "UPDATE_INTERVAL_DEFAULT",
    "UPDATE_INTERVAL_CHOICES",
    "TIMEFRAME_DEFAULT",
    "TIMEFRAME_CHOICES",
]

_no_timeframe = 0
_hour = 60
_day = _hour * 24

_PAGE_SIZES_FALLBACK = [10, 20, 50, 100]
_PAGE_SIZES = getattr(settings, "ARGUS_INCIDENTS_PAGE_SIZES", _PAGE_SIZES_FALLBACK)
PAGE_SIZE_DEFAULT = getattr(settings, "ARGUS_INCIDENTS_DEFAULT_PAGE_SIZE", 10)
PAGE_SIZE_CHOICES = tuple((ps, ps) for ps in _PAGE_SIZES)

_UPDATE_INTERVAL_FALLBACK = ["never", 5, 30, 60]
UPDATE_INTERVAL_DEFAULT = getattr(settings, "ARGUS_INCIDENTS_UPDATE_INTERVAL_DEFAULT", 30)
_UPDATE_INTERVALS = getattr(settings, "ARGUS_INCIDENTS_UPDATE_INTERVALS", _UPDATE_INTERVAL_FALLBACK)
UPDATE_INTERVAL_CHOICES = tuple((interval, update_interval_string(interval)) for interval in _UPDATE_INTERVALS)

TIMEFRAME_DEFAULT = _no_timeframe
TIMEFRAME_CHOICES = (
    (_no_timeframe, "None"),
    (_hour, "Last hour"),
    (_hour * 3, "Last 3 hours"),
    (_hour * 12, "Last 12 hours"),
    (_day, "Last 24 hours"),
    (_day * 7, "Last week"),
    (_day * 30, "Last 30 days"),
)

_INCIDENTS_TABLE_LAYOUT_ALLOWED = ["standard", "compact"]
INCIDENTS_TABLE_LAYOUT_CHOICES = tuple((layout, layout) for layout in _INCIDENTS_TABLE_LAYOUT_ALLOWED)
INCIDENTS_TABLE_LAYOUT_DEFAULT = getattr(settings, "ARGUS_INCIDENTS_TABLE_LAYOUT_DEFAULT", "compact")
