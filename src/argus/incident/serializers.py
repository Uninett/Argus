from rest_framework import serializers

from .models import (
    ActiveIncident,
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
    source = SourceSystemSerializer(read_only=True)
    object = ObjectSerializer()
    parent_object = ParentObjectSerializer()
    problem_type = ProblemTypeSerializer()
    active_state = serializers.BooleanField()

    class Meta:
        model = Incident
        fields = [
            "pk",
            "timestamp",
            "source",
            "source_incident_id",
            "object",
            "parent_object",
            "details_url",
            "problem_type",
            "description",
            "ticket_url",
            "active_state",
        ]
        read_only_fields = ["pk"]

    def create(self, validated_data):
        assert "source" in validated_data
        source = validated_data["source"]

        object_data = validated_data.pop("object")
        object_type_data = object_data.pop("type")
        parent_object_data = validated_data.pop("parent_object")
        problem_type_data = validated_data.pop("problem_type")
        active_state = validated_data.pop("active_state")

        object_type, _created = ObjectType.objects.get_or_create(**object_type_data)
        object_, _created = Object.objects.get_or_create(source_system=source, type=object_type, **object_data)
        parent_object, _created = ParentObject.objects.get_or_create(**parent_object_data)
        problem_type, _created = ProblemType.objects.get_or_create(**problem_type_data)

        incident = Incident.objects.create(
            object=object_, parent_object=parent_object, problem_type=problem_type, **validated_data,
        )
        if active_state:
            ActiveIncident.objects.create(incident=incident)

        return incident

    def to_representation(self, instance: Incident):
        incident_repr = super().to_representation(instance)
        incident_repr["active_state"] = hasattr(instance, "active_state")
        return incident_repr
