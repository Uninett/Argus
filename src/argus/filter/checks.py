from django.conf import settings
from django.core.checks import Warning

from rest_framework import serializers

from argus.filter.validators import validate_jsonfilter


__all__ = ["fallback_filter_check"]


def fallback_filter_check(app_configs, **kwargs):
    fallback_filter = getattr(settings, "ARGUS_FALLBACK_FILTER", {})
    try:
        validate_jsonfilter(fallback_filter)
    except serializers.ValidationError:
        warning = Warning(
            'The ARGUS_FALLBACK_FILTER setting is invalid and has been set to "{}"',
            hint="See the docs for the format of the ARGUS_FALLBACK_FILTER setting",
            obj=fallback_filter,
            id="argus_filter.W001",
        )
        return [warning]
    else:
        return []
