from django.conf import settings


__all__ = [
    "DEFAULT_PAGE_SIZE",
    "ALLOWED_PAGE_SIZES",
    "PAGE_SIZE_CHOICES",
    "INCIDENTS_TABLE_LAYOUT_ALLOWED",
    "INCIDENTS_TABLE_LAYOUT_CHOICES",
    "INCIDENTS_TABLE_LAYOUT_DEFAULT",
    "UPDATE_INTERVAL_DEFAULT",
    "UPDATE_INTERVAL_ALLOWED",
    "UPDATE_INTERVAL_CHOICES",
    "TIMEFRAME_DEFAULT",
    "TIMEFRAME_CHOICES",
]

_no_timeframe = 0
_hour = 60
_day = _hour * 24


DEFAULT_PAGE_SIZE = getattr(settings, "ARGUS_INCIDENTS_DEFAULT_PAGE_SIZE", 10)
ALLOWED_PAGE_SIZES = getattr(settings, "ARGUS_INCIDENTS_PAGE_SIZES", [10, 20, 50, 100])
PAGE_SIZE_CHOICES = tuple((ps, ps) for ps in ALLOWED_PAGE_SIZES)

UPDATE_INTERVAL_DEFAULT = getattr(settings, "ARGUS_INCIDENTS_UPDATE_INTERVAL_DEFAULT", 30)
UPDATE_INTERVAL_ALLOWED = getattr(settings, "ARGUS_INCIDENTS_UPDATE_INTERVALS", ["never", 5, 30, 60])
UPDATE_INTERVAL_CHOICES = tuple((interval, interval) for interval in UPDATE_INTERVAL_ALLOWED)

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

INCIDENTS_TABLE_LAYOUT_ALLOWED = ["standard", "compact"]
INCIDENTS_TABLE_LAYOUT_CHOICES = tuple((layout, layout) for layout in INCIDENTS_TABLE_LAYOUT_ALLOWED)
INCIDENTS_TABLE_LAYOUT_DEFAULT = getattr(settings, "ARGUS_INCIDENTS_TABLE_LAYOUT_DEFAULT", "compact")
