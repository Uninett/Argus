from rest_framework import serializers

from .models import Alert, NetworkSystem, Object, ObjectType, ParentObject, ProblemType


class NetworkSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkSystem
        fields = ['pk', 'name', 'type']
        read_only_fields = ['pk', 'type']

    def to_representation(self, instance: NetworkSystem):
        representation = super().to_representation(instance)
        representation['type'] = instance.get_type_display()
        return representation


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

    # type = ObjectTypeSerializer(read_only=True)

    def to_representation(self, instance: Object):
        representation = super().to_representation(instance)
        representation['type'] = ObjectTypeSerializer(instance.type).data
        return representation


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

    # TODO: make these return a normal dict instead of an OrderedDict
    # source = NetworkSystemSerializer(read_only=True)
    # object = ObjectSerializer(read_only=True)
    # parent_object = ParentObjectSerializer(read_only=True)
    # problem_type = ProblemTypeSerializer(read_only=True)

    def to_representation(self, instance: Alert):
        representation = super().to_representation(instance)
        representation['source'] = NetworkSystemSerializer(instance.source).data
        representation['object'] = ObjectSerializer(instance.object).data
        representation['parent_object'] = ParentObjectSerializer(instance.parent_object).data
        representation['problem_type'] = ProblemTypeSerializer(instance.problem_type).data
        representation['active_state'] = hasattr(instance, 'active_state')
        return representation
