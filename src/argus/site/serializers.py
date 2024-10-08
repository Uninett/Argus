from typing import Any

from rest_framework import serializers


class MetadataSerializer(serializers.Serializer):
    server_version = serializers.CharField()
    api_version = serializers.DictField(child=serializers.CharField(), read_only=True)
    jsonapi_schema = serializers.DictField(child=serializers.CharField(), read_only=True)
    ticket_plugin = serializers.CharField(read_only=True, allow_null=True)
    destination_plugins = serializers.ListField(child=serializers.CharField(), read_only=True, allow_empty=True)

    def get_fields(self) -> dict[str, Any]:
        fields = super().get_fields()
        fields["server-version"] = fields.pop("server_version")
        fields["api-version"] = fields.pop("api_version")
        fields["jsonapi-schema"] = fields.pop("jsonapi_schema")
        return fields
