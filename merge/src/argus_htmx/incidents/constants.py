from django.conf import settings


__all__ = [
    "DEFAULT_PAGE_SIZE",
    "ALLOWED_PAGE_SIZES",
    "PAGE_SIZE_CHOICES",
]


DEFAULT_PAGE_SIZE = getattr(settings, "ARGUS_INCIDENTS_DEFAULT_PAGE_SIZE", 10)
ALLOWED_PAGE_SIZES = getattr(settings, "ARGUS_INCIDENTS_PAGE_SIZES", [10, 20, 50, 100])
PAGE_SIZE_CHOICES = tuple((ps, ps) for ps in ALLOWED_PAGE_SIZES)
