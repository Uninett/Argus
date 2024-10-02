from rest_framework import serializers

from argus.incident.constants import Level
from argus.incident.models import Event
from ..primitive_serializers import CustomMultipleChoiceField


__all__ = [
    "FilterBlobSerializer",
]


class FilterBlobSerializer(serializers.Serializer):
    sourceSystemIds = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        required=False,
    )
    tags = serializers.ListField(
        child=serializers.CharField(min_length=3),
        allow_empty=True,
        required=False,
    )
    open = serializers.BooleanField(required=False, allow_null=True)
    acked = serializers.BooleanField(required=False, allow_null=True)
    stateful = serializers.BooleanField(required=False, allow_null=True)
    maxlevel = serializers.IntegerField(
        required=False, allow_null=True, max_value=max(Level).value, min_value=min(Level).value
    )
    event_types = CustomMultipleChoiceField(
        choices=Event.Type.choices,
        required=False,
    )
