from rest_framework import serializers

from argus.filter import get_filter_backend

filter_backend = get_filter_backend()
FilterBlobSerializer = filter_backend.FilterBlobSerializer


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
