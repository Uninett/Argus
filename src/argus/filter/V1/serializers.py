import json
from typing import List

from rest_framework import fields, serializers
from rest_framework import serializers

from argus.incident.constants import INCIDENT_LEVELS
from argus.notificationprofile.models import Filter

from ..primitive_serializers import CustomMultipleChoiceField
from .validators import validate_filter_string


class FilterPreviewSerializer(serializers.Serializer):
    sourceSystemIds = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=True)
    tags = serializers.ListField(child=serializers.CharField(min_length=3), allow_empty=True)


class FilterBlobSerializerV1(serializers.Serializer):
    sourceSystemIds = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        required=False,
    )
    tags = serializers.ListField(
        child=serializers.CharField(min_length=3),
        allow_empty=True,
        required=False,
    )
    open = serializers.BooleanField(required=False, allow_null=True)
    acked = serializers.BooleanField(required=False, allow_null=True)
    stateful = serializers.BooleanField(required=False, allow_null=True)
    maxlevel = serializers.IntegerField(
        required=False, allow_null=True, max_value=max(INCIDENT_LEVELS), min_value=min(INCIDENT_LEVELS)
    )


class FilterSerializerV1(serializers.ModelSerializer):
    filter_string = serializers.CharField(
        validators=[validate_filter_string],
        help_text='Deprecated: Use "filter" instead',
        required=False,
    )
    filter = FilterBlobSerializerV1(required=False)

    class Meta:
        model = Filter
        fields = [
            "pk",
            "name",
            "filter_string",
            "filter",
        ]

    def _copy_content_from_filter_string_to_filter(self, validated_data):
        if "filter_string" in validated_data.keys():
            filter_string_dict = json.loads(validated_data.pop("filter_string"))
            if "filter" not in validated_data.keys():
                validated_data["filter"] = filter_string_dict
            else:
                filter_dict = validated_data["filter"]
                source_system_ids = filter_string_dict["sourceSystemIds"]
                if source_system_ids and ("sourceSystemIds" not in filter_dict.keys()):
                    validated_data["filter"]["sourceSystemIds"] = source_system_ids

                tags = filter_string_dict["tags"]
                if tags and "tags" not in filter_dict.keys():
                    validated_data["filter"]["tags"] = tags
        return validated_data

    def create(self, validated_data):
        validated_data = self._copy_content_from_filter_string_to_filter(validated_data=validated_data)
        return Filter.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data = self._copy_content_from_filter_string_to_filter(validated_data=validated_data)
        return super().update(instance=instance, validated_data=validated_data)

    def to_representation(self, obj):
        filter_string_dict = {"sourceSystemIds": [], "tags": []}
        filter_keys = obj.filter.keys()
        if "sourceSystemIds" in filter_keys:
            filter_string_dict["sourceSystemIds"] = obj.filter["sourceSystemIds"]
        if "tags" in filter_keys:
            filter_string_dict["tags"] = obj.filter["tags"]
        obj.filter_string = json.dumps(filter_string_dict)

        return super().to_representation(obj)
