from rest_framework import serializers

from argus.notificationprofile.models import Filter
from argus.filter import get_filter_backend

filter_backend = get_filter_backend()
FilterBlobSerializer = filter_backend.FilterBlobSerializer


__all__ = [
    "FilterSerializer",
]


class FilterSerializer(serializers.ModelSerializer):
    filter = FilterBlobSerializer(required=False)

    class Meta:
        model = Filter
        fields = [
            "pk",
            "name",
            "filter",
        ]
