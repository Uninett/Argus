from rest_framework import fields, serializers

from argus.incident.constants import INCIDENT_LEVELS
from argus.incident.models import Event
from argus.notificationprofile.models import Filter
from .primitive_serializers import CustomMultipleChoiceField


__all__ = [
    "FilterBlobSerializer",
    "FilterSerializer",
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
        required=False, allow_null=True, max_value=max(INCIDENT_LEVELS), min_value=min(INCIDENT_LEVELS)
    )
    event_types = CustomMultipleChoiceField(
        choices=Event.Type.choices,
        required=False,
    )


class FilterSerializer(serializers.ModelSerializer):
    filter = FilterBlobSerializer(required=False)

    class Meta:
        model = Filter
        fields = [
            "pk",
            "name",
            "filter",
        ]
