from rest_framework import serializers

from ..fields import DateTimeInfinitySerializerField
from ..models import Incident
from ..serializers import IncidentSerializer, SourceSystemSerializer, IncidentTagRelationSerializer


class IncidentSerializerV1(IncidentSerializer):
    end_time = DateTimeInfinitySerializerField(required=False, allow_null=True)
    source = SourceSystemSerializer(read_only=True)
    tags = IncidentTagRelationSerializer(many=True, write_only=True, source="deprecated_tags")

    class Meta:
        model = Incident
        fields = [
            "pk",
            "start_time",
            "end_time",
            "source",
            "source_incident_id",
            "details_url",
            "description",
            "level",
            "ticket_url",
            "tags",
        ]
        read_only_fields = ["source"]
        extra_kwargs = {"level": {"required": False}}


# Get rid of this!
class MetadataSerializer(serializers.Serializer):
    sourceSystems = SourceSystemSerializer(many=True)
