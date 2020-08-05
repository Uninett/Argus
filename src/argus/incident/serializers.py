from django.core.validators import URLValidator
from rest_framework import serializers

from . import fields
from .models import (
    Incident,
    Object,
    ObjectType,
    ParentObject,
    ProblemType,
    SourceSystem,
    SourceSystemType,
)


class RemovableFieldSerializer(serializers.ModelSerializer):
    NO_PKS_KEY = "no_pks"

    def to_representation(self, instance):
        obj_repr = super().to_representation(instance)

        if self.NO_PKS_KEY in self.context:
            obj_repr.pop("pk")
        return obj_repr


class SourceSystemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceSystemType
        fields = ["name"]


class SourceSystemSerializer(RemovableFieldSerializer):
    type = SourceSystemTypeSerializer(read_only=True)

    class Meta:
        model = SourceSystem
        fields = ["pk", "name", "type", "user"]
        read_only_fields = ["pk", "type", "user"]


class ObjectTypeSerializer(RemovableFieldSerializer):
    class Meta:
        model = ObjectType
        fields = ["pk", "name"]
        read_only_fields = ["pk"]


class ObjectSerializer(RemovableFieldSerializer):
    type = ObjectTypeSerializer()

    class Meta:
        model = Object
        fields = ["pk", "name", "object_id", "url", "type"]
        read_only_fields = ["pk"]


class ParentObjectSerializer(RemovableFieldSerializer):
    class Meta:
        model = ParentObject
        fields = ["pk", "name", "parentobject_id", "url"]
        read_only_fields = ["pk"]


class ProblemTypeSerializer(RemovableFieldSerializer):
    class Meta:
        model = ProblemType
        fields = ["pk", "name", "description"]
        read_only_fields = ["pk"]


class IncidentSerializer(RemovableFieldSerializer):
    end_time = fields.DateTimeInfinitySerializerField(required=False, allow_null=True)
    source = SourceSystemSerializer(read_only=True)
    object = ObjectSerializer()
    parent_object = ParentObjectSerializer()
    problem_type = ProblemTypeSerializer()

    class Meta:
        model = Incident
        fields = [
            "pk",
            "start_time",
            "end_time",
            "source",
            "source_incident_id",
            "object",
            "parent_object",
            "details_url",
            "problem_type",
            "description",
            "ticket_url",
        ]
        read_only_fields = ["pk"]

    def create(self, validated_data):
        assert "source" in validated_data
        source = validated_data["source"]

        object_data = validated_data.pop("object")
        object_type_data = object_data.pop("type")
        parent_object_data = validated_data.pop("parent_object")
        problem_type_data = validated_data.pop("problem_type")

        object_type, _created = ObjectType.objects.get_or_create(**object_type_data)
        object_, _created = Object.objects.get_or_create(source_system=source, type=object_type, **object_data)
        parent_object, _created = ParentObject.objects.get_or_create(**parent_object_data)
        problem_type, _created = ProblemType.objects.get_or_create(**problem_type_data)

        return Incident.objects.create(
            object=object_, parent_object=parent_object, problem_type=problem_type, **validated_data,
        )

    def to_representation(self, instance: Incident):
        incident_repr = super().to_representation(instance)
        incident_repr["stateful"] = instance.stateful
        incident_repr["active"] = instance.active
        return incident_repr

    def validate_ticket_url(self, value):
        validator = URLValidator()
        validator(value)
        return value


# TODO: remove once it's not in use anymore
class IncidentSerializer_legacy(RemovableFieldSerializer):
    source = SourceSystemSerializer(read_only=True)
    object = ObjectSerializer(read_only=True)
    parent_object = ParentObjectSerializer(read_only=True)
    problem_type = ProblemTypeSerializer(read_only=True)

    class Meta:
        model = Incident
        fields = [
            "pk",
            "start_time",
            "end_time",
            "source",
            "source_incident_id",
            "object",
            "parent_object",
            "details_url",
            "problem_type",
            "description",
            "ticket_url",
        ]
        read_only_fields = ["pk"]
