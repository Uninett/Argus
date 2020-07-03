from rest_framework import serializers

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
    type = ObjectTypeSerializer(read_only=True)

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
    object = ObjectSerializer(read_only=True)
    parent_object = ParentObjectSerializer(read_only=True)
    problem_type = ProblemTypeSerializer(read_only=True)

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
        read_only_fields = ["pk", "active_state"]

    def to_representation(self, instance: Incident):
        incident_repr = super().to_representation(instance)
        incident_repr["active_state"] = hasattr(instance, "active_state")
        return incident_repr
