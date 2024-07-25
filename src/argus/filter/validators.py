from rest_framework import serializers

from argus.filter.serializers import FilterBlobSerializer


__all__ = [
    "validate_jsonfilter",
]


def validate_jsonfilter(value: dict):
    if not isinstance(value, dict):
        raise serializers.ValidationError("Filter is not a dict")
    if not value:
        return True
    serializer = FilterBlobSerializer(data=value)
    if serializer.is_valid():
        return True
    raise serializers.ValidationError("Filter is not valid")
