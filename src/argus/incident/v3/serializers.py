from collections.abc import Iterable

from django.contrib.auth import get_user_model
from django.db import models

from rest_framework import serializers

from argus.incident.factories import set_tags_on_incident, add_tags_to_incident
from argus.incident.models import (
    Incident,
    SourceSystem,
)
from argus.incident.validators import validate_tagstring
from argus.incident.v2.serializers import (
    SourceSystemTypeSerializer,
    IncidentSerializer as IncidentSerializerV2,
    IncidentPureDeserializer as IncidentPureDeserializerV2,
)


User = get_user_model()


VERSION = "v3"


class SourceSystemSerializer(serializers.ModelSerializer):
    type = SourceSystemTypeSerializer(read_only=True)

    class Meta:
        model = SourceSystem
        fields = ["pk", "name", "type", "user", "base_url", "last_seen"]
        read_only_fields = ["type", "user", "base_url", "last_seen"]


class TagListSerializer(serializers.ListSerializer):
    child = serializers.CharField(
        min_length=2,
        required=False,
        validators=[validate_tagstring],
        write_only=True,
    )

    def to_representation(self, data):
        """List of object instances -> List of strings"""
        output = []
        if not data:
            return output

        if isinstance(data, models.manager.BaseManager):
            iterable = data.all()
        elif isinstance(data, str) or not isinstance(data, Iterable):
            iterable = [data]
        else:
            iterable = data
        for item in iterable:
            output.append(self.child.to_representation(item))
        return output


class IncidentSerializer(IncidentSerializerV2):
    source = SourceSystemSerializer(read_only=True)
    tags = TagListSerializer()

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
            "metadata",
        ]
        read_only_fields = ["source"]

    def create(self, validated_data: dict):
        validated_data.pop("user")
        tags_data = validated_data.pop("tags", [])

        incident = Incident.objects.create(**validated_data)
        add_tags_to_incident(incident, *tags_data)
        incident.create_first_event()

        return incident

    def to_representation(self, instance: Incident):
        incident_repr = super().to_representation(instance)

        tag_relations = instance.incident_tag_relations.all()
        incident_repr["tags"] = [tagrel.tag.representation for tagrel in tag_relations]

        incident_repr["details_url"] = instance.pp_details_url()

        incident_repr["stateful"] = instance.stateful
        incident_repr["open"] = instance.open
        incident_repr["acked"] = instance.acked
        return incident_repr


#


class IncidentPureDeserializer(IncidentPureDeserializerV2):
    tags = TagListSerializer()

    class Meta:
        model = Incident
        fields = [
            "tags",
            "details_url",
            "ticket_url",
            "level",
            "metadata",
            "description",
        ]

    def update(self, instance: Incident, validated_data: dict):
        assert "user" in validated_data
        user: User = validated_data["user"]
        tagstrings = validated_data.pop("tags", [])

        if tagstrings:
            set_tags_on_incident(instance, user=user, *tagstrings)

        if self.EDITABLE_FIELDS.intersection(validated_data):
            self.post_change_events(instance, user, validated_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance: Incident):
        return IncidentSerializer(instance).data
