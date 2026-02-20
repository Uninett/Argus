from rest_framework import serializers

from argus.notificationprofile.media import api_safely_get_medium_object
from argus.notificationprofile.models import DestinationConfig
from argus.notificationprofile.v2.serializers import MediaSerializer


VERSION = "v3"


class DestinationConfigSerializer(serializers.ModelSerializer):
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
