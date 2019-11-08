from rest_framework import serializers

from .models import Alert, NetworkSystem, NetworkSystemType, Object, ObjectType, ParentObject, ProblemType


class NetworkSystemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkSystemType
        fields = ['name']


class NetworkSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkSystem
        fields = ['name', 'type']

    # type = NetworkSystemTypeSerializer(read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = NetworkSystemTypeSerializer(instance.type).data
        return representation


class ObjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectType
        fields = ['name']


class ObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Object
        fields = ['name', 'object_id', 'url', 'type']

    # type = ObjectTypeSerializer(read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['type'] = ObjectTypeSerializer(instance.type).data
        return representation


class ParentObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentObject
        fields = ['name', 'parentobject_id', 'url']


class ProblemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemType
        fields = ['name', 'description']


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ['pk', 'timestamp', 'source', 'alert_id', 'object', 'parent_object', 'details_url', 'problem_type', 'description', 'ticket_url']
        read_only_fields = ['pk']

    # TODO: make these return a normal dict instead of an OrderedDict
    # source = NetworkSystemSerializer(read_only=True)
    # object = ObjectSerializer(read_only=True)
    # parent_object = ParentObjectSerializer(read_only=True)
    # problem_type = ProblemTypeSerializer(read_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['source'] = NetworkSystemSerializer(instance.source).data
        representation['object'] = ObjectSerializer(instance.object).data
        representation['parent_object'] = ParentObjectSerializer(instance.parent_object).data
        representation['problem_type'] = ProblemTypeSerializer(instance.problem_type).data
        return representation
