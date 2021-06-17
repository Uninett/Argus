from rest_framework import serializers

from ..models import Incident
from ..serializers import IncidentSerializer, SourceSystemSerializer


class IncidentSerializerV1(IncidentSerializer):
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
