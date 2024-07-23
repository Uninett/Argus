from django.conf import settings
from django.core.checks import Warning

from argus.filter import get_filter_backend

filter_backend = get_filter_backend()
validate_jsonfilter = filter_backend.validate_jsonfilter


__all__ = ["fallback_filter_check"]


def fallback_filter_check(app_configs, **kwargs):
    errors = []
    fallback_filter = getattr(settings, "ARGUS_FALLBACK_FILTER", {})
    if not validate_jsonfilter(fallback_filter):
        errors.append(
            Warning(
                'The ARGUS_FALLBACK_FILTER setting is invalid and has been set to "{}"',
                hint="See the docs for the format of the ARGUS_FALLBACK_FILTER setting",
                obj=fallback_filter,
                id="argus_filter.W001",
            )
        )
    return errors
