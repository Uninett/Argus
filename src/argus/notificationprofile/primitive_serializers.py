from rest_framework import serializers


class CustomMultipleChoiceField(serializers.MultipleChoiceField):
    def to_internal_value(self, value):
        return list(super().to_internal_value(value))


class FilterPreviewSerializer(serializers.Serializer):
    sourceSystemIds = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=True)
    tags = serializers.ListField(child=serializers.CharField(min_length=3), allow_empty=True)
