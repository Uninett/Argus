from rest_framework import serializers

from .models import Alert, NetworkSystem, Object, ObjectType, ParentObject, ProblemType


class NetworkSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkSystem
        fields = ['pk', 'name', 'type']
        read_only_fields = ['pk', 'type']

    def to_representation(self, instance: NetworkSystem):
        system_repr = super().to_representation(instance)
        system_repr['type'] = instance.get_type_display()
        return system_repr


class ObjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectType
        fields = ['pk', 'name']
        read_only_fields = ['pk']


class ObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Object
        fields = ['pk', 'name', 'object_id', 'url', 'type']
        read_only_fields = ['pk']

    type = ObjectTypeSerializer(read_only=True)


class ParentObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentObject
        fields = ['pk', 'name', 'parentobject_id', 'url']
        read_only_fields = ['pk']


class ProblemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemType
        fields = ['pk', 'name', 'description']
        read_only_fields = ['pk']


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ['pk', 'timestamp', 'source', 'alert_id', 'object', 'parent_object', 'details_url', 'problem_type', 'description', 'ticket_url', 'active_state']
        read_only_fields = ['pk', 'active_state']

    source = NetworkSystemSerializer(read_only=True)
    object = ObjectSerializer(read_only=True)
    parent_object = ParentObjectSerializer(read_only=True)
    problem_type = ProblemTypeSerializer(read_only=True)

    def to_representation(self, instance: Alert):
        alert_repr = super().to_representation(instance)
        alert_repr['active_state'] = hasattr(instance, 'active_state')
        return alert_repr
