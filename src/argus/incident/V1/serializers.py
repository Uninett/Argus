from rest_framework import serializers

from ..fields import DateTimeInfinitySerializerField
from ..models import Incident, Tag, IncidentTagRelation
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

    def create(self, validated_data: dict):
        assert "user" in validated_data
        user = validated_data.pop("user")

        tags_data = validated_data.pop("deprecated_tags")
        tags = {Tag.objects.get_or_create(**tag_data)[0] for tag_data in tags_data}

        incident = Incident.objects.create(**validated_data)
        for tag in tags:
            IncidentTagRelation.objects.create(tag=tag, incident=incident, added_by=user)

        return incident


# Get rid of this!
class MetadataSerializer(serializers.Serializer):
    sourceSystems = SourceSystemSerializer(many=True)
