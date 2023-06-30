from django.utils import timezone

from rest_framework import serializers

from ..fields import DateTimeInfinitySerializerField
from ..models import (
    Acknowledgement,
    Event,
    Incident,
    Tag,
    IncidentTagRelation,
)
from ..serializers import (
    EventSerializer,
    IncidentSerializer,
    SourceSystemSerializer,
    IncidentTagRelationSerializer,
)


class IncidentSerializerV1(IncidentSerializer):
    end_time = DateTimeInfinitySerializerField(required=False, allow_null=True)
    source = SourceSystemSerializer(read_only=True)
    tags = IncidentTagRelationSerializer(many=True, write_only=True, source="deprecated_tags")

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
        ]
        read_only_fields = ["source"]
        extra_kwargs = {"level": {"required": False}}

    def create(self, validated_data: dict):
        assert "user" in validated_data
        user = validated_data.pop("user")

        tags_data = validated_data.pop("deprecated_tags")
        tags = {Tag.objects.get_or_create(**tag_data)[0] for tag_data in tags_data}

        incident = Incident.objects.create(**validated_data)
        for tag in tags:
            IncidentTagRelation.objects.create(tag=tag, incident=incident, added_by=user)
        incident.create_first_event()

        return incident


class AcknowledgementSerializerV1(serializers.ModelSerializer):
    event = EventSerializer()

    class Meta:
        model = Acknowledgement
        fields = [
            "pk",
            "event",
            "expiration",
        ]
        # "pk" needs to be listed, as "event" is the actual primary key
        read_only_fields = ["pk"]

    def create(self, validated_data: dict):
        assert "incident" in validated_data, '"incident" not in input'
        assert "actor" in validated_data, '"actor" not in input'
        incident = validated_data.pop("incident")
        actor = validated_data.pop("actor")
        expiration = validated_data.get("expiration", None)
        event_data = validated_data.pop("event")
        timestamp = event_data.pop("timestamp")
        description = event_data.get("description", "")
        ack = incident.create_ack(actor, timestamp=timestamp, description=description, expiration=expiration)
        return ack

    def to_internal_value(self, data: dict):
        data["event"]["type"] = Event.Type.ACKNOWLEDGE
        return super().to_internal_value(data)

    def validate_event(self, value: dict):
        event_type = value["type"]
        if event_type != Event.Type.ACKNOWLEDGE:
            raise serializers.ValidationError(
                f"'{event_type}' is not a valid event type for acknowledgements."
                f" Use '{Event.Type.ACKNOWLEDGE}' or omit 'type' completely."
            )
        return value

    def validate(self, attrs: dict):
        expiration = attrs.get("expiration")
        if expiration and expiration <= attrs["event"]["timestamp"]:
            raise serializers.ValidationError("'expiration' is earlier than creation timestamp.")
        return attrs


class UpdateAcknowledgementSerializerV1(serializers.ModelSerializer):
    _later_than_func = timezone.now

    class Meta:
        model = Acknowledgement
        fields = [
            "expiration",
        ]

    def update(self, instance, validated_data):
        now = self.__class__._later_than_func()
        if instance.expiration and instance.expiration < now:  # expired are readonly
            raise serializers.ValidationError(f"Cannot change expired Acknowledgement")
        expiration = validated_data.get("expiration")
        instance.expiration = expiration
        instance.save()
        return instance

    def validate_expiration(self, expiration):
        now = self.__class__._later_than_func()
        if expiration and expiration <= now:
            raise serializers.ValidationError(f"'expiration' must be later than current moment ({now}) or null.")
        return expiration

    def to_representation(self, instance):
        serializer = AcknowledgementSerializerV1(instance=instance)
        return serializer.data


# Get rid of this!
class MetadataSerializer(serializers.Serializer):
    sourceSystems = SourceSystemSerializer(many=True)
