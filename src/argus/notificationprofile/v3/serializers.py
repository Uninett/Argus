from rest_framework import serializers

from argus.notificationprofile.media import api_safely_get_medium_object
from argus.notificationprofile.models import DestinationConfig
from argus.notificationprofile.v2.serializers import MediaSerializer


VERSION = "v3"


class ResponseDestinationConfigSerializer(serializers.ModelSerializer):
    version = VERSION

    media = MediaSerializer()
    suggested_label = serializers.SerializerMethodField(method_name="get_suggested_label")
    managed = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = DestinationConfig
        fields = [
            "pk",
            "media",
            "label",
            "suggested_label",
            "settings",
            "managed",
        ]

    def get_suggested_label(self, destination: DestinationConfig) -> str:
        medium = api_safely_get_medium_object(destination.media.slug, VERSION)
        return f"{destination.media.name}: {medium.get_label(destination)}"


class RequestDestinationConfigSerializer(serializers.ModelSerializer):
    version = VERSION

    class Meta:
        model = DestinationConfig
        fields = [
            "media",
            "label",
            "settings",
        ]

    def validate(self, attrs: dict):
        if self.instance and "media" in attrs.keys() and not attrs["media"].slug == self.instance.media.slug:
            raise serializers.ValidationError("Media cannot be updated, only settings.")
        if "settings" in attrs.keys():
            if not isinstance(attrs["settings"], dict):
                raise serializers.ValidationError("Settings has to be a dictionary.")
            if self.instance:
                medium = api_safely_get_medium_object(self.instance.media.slug, self.version)
            else:
                medium = api_safely_get_medium_object(attrs["media"].slug, self.version)
            attrs["settings"] = medium.validate(self, attrs, self.context["request"].user)

        return attrs

    def update(self, destination: DestinationConfig, validated_data: dict):
        medium = api_safely_get_medium_object(destination.media.slug, self.version)
        updated_destination = medium.update(destination, validated_data)

        return updated_destination
