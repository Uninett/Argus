from django.contrib.auth import get_user_model

from rest_framework import serializers

from argus.incident.models import (
    Incident,
    SourceSystem,
)
from argus.incident.v2.serializers import (
    SourceSystemTypeSerializer,
    IncidentSerializer as IncidentSerializerV2,
    IncidentPureDeserializer,  # noqa: F401
)


User = get_user_model()


VERSION = "v3"


class SourceSystemSerializer(serializers.ModelSerializer):
    type = SourceSystemTypeSerializer(read_only=True)

    class Meta:
        model = SourceSystem
        fields = ["pk", "name", "type", "user", "base_url", "last_seen"]
        read_only_fields = ["type", "user", "base_url", "last_seen"]


class IncidentSerializer(IncidentSerializerV2):
    source = SourceSystemSerializer(read_only=True)

    class Meta:
        model = Incident
        fields = [
            "pk",
            "start_time",
            "end_time",
            "source",
            "source_incident_id",
            "details_url",
            "description",
            "level",
            "ticket_url",
            "tags",
            "metadata",
        ]
        read_only_fields = ["source"]
