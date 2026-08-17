from rest_framework import serializers

from argus.notificationprofile.media import safely_get_medium_object
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
        medium = safely_get_medium_object(destination.media.slug)
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
        media_slug = self.instance.media.slug if self.instance else attrs["media"].slug
        medium = safely_get_medium_object(media_slug)
        form = medium.validate(attrs, self.context["request"].user, self.instance)

        return form.cleaned_data

    def update(self, destination: DestinationConfig, validated_data: dict):
        medium = safely_get_medium_object(destination.media.slug)
        updated_destination = medium.update(destination, validated_data)

        return updated_destination
