from rest_framework import serializers

from argus.incident.constants import INCIDENT_LEVELS
from argus.incident.models import Event


class CustomMultipleChoiceField(serializers.MultipleChoiceField):
    def to_internal_value(self, value):
        return list(super().to_internal_value(value))


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


class FilterPreviewSerializer(serializers.Serializer):
    sourceSystemIds = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=True)
    tags = serializers.ListField(child=serializers.CharField(min_length=3), allow_empty=True)
