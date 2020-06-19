from rest_framework import serializers

from .models import (
    Alert,
    AlertSource,
    AlertSourceType,
    Object,
    ObjectType,
    ParentObject,
    ProblemType,
)


class RemovableFieldSerializer(serializers.ModelSerializer):
    NO_PKS_KEY = "no_pks"

    def to_representation(self, instance):
        obj_repr = super().to_representation(instance)

        if self.NO_PKS_KEY in self.context:
            obj_repr.pop("pk")
        return obj_repr


class AlertSourceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertSourceType
        fields = ["name"]


class AlertSourceSerializer(RemovableFieldSerializer):
    class Meta:
        model = AlertSource
        fields = ["pk", "name", "type"]
        read_only_fields = ["pk", "type"]

    type = AlertSourceTypeSerializer(read_only=True)


class ObjectTypeSerializer(RemovableFieldSerializer):
    class Meta:
        model = ObjectType
        fields = ["pk", "name"]
        read_only_fields = ["pk"]


class ObjectSerializer(RemovableFieldSerializer):
    class Meta:
        model = Object
        fields = ["pk", "name", "object_id", "url", "type"]
        read_only_fields = ["pk"]

    type = ObjectTypeSerializer(read_only=True)


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


class AlertSerializer(RemovableFieldSerializer):
    class Meta:
        model = Alert
        fields = [
            "pk",
            "timestamp",
            "source",
            "alert_id",
            "object",
            "parent_object",
            "details_url",
            "problem_type",
            "description",
            "ticket_url",
            "active_state",
        ]
        read_only_fields = ["pk", "active_state"]

    source = AlertSourceSerializer(read_only=True)
    object = ObjectSerializer(read_only=True)
    parent_object = ParentObjectSerializer(read_only=True)
    problem_type = ProblemTypeSerializer(read_only=True)

    def to_representation(self, instance: Alert):
        alert_repr = super().to_representation(instance)
        alert_repr["active_state"] = hasattr(instance, "active_state")
        return alert_repr
