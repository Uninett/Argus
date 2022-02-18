from django.db import IntegrityError
from rest_framework import fields, serializers

from ..models import NotificationProfile
from ..serializers import (
    TimeslotSerializer,
    FilterSerializer,
)


class ResponseNotificationProfileSerializerV1(serializers.ModelSerializer):
    timeslot = TimeslotSerializer()
    filters = FilterSerializer(many=True)
    phone_number = serializers.SerializerMethodField("get_phone_number")
    # media = fields.MultipleChoiceField(choices=NotificationProfile.Media.choices, source="media_v1")

    class Meta:
        model = NotificationProfile
        fields = [
            "pk",
            "timeslot",
            "filters",
            "media",
            "phone_number",
            "active",
        ]
        # "pk" needs to be listed, as "timeslot" is the actual primary key
        read_only_fields = ["pk"]

    def get_phone_number(self, profile: NotificationProfile):
        if profile.destinations.filter(media__slug="sms").exists():
            return profile.destinations.filter(media__slug="sms").order_by("pk")[0].settings["phone_number"]
        return None


class RequestNotificationProfileSerializerV1(serializers.ModelSerializer):
    # media = fields.MultipleChoiceField(choices=NotificationProfile.Media.choices, source="media_v1")
    phone_number = fields.CharField(allow_null=True, required=False)

    class Meta:
        model = NotificationProfile
        fields = [
            "pk",
            "timeslot",
            "filters",
            "media",
            "phone_number",
            "active",
        ]
        # "pk" needs to be listed, as "timeslot" is the actual primary key
        read_only_fields = ["pk"]

    def create(self, validated_data: dict):
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            timeslot_pk = validated_data["timeslot"].pk
            if NotificationProfile.objects.filter(pk=timeslot_pk).exists():
                raise serializers.ValidationError(
                    f"NotificationProfile with Timeslot with pk={timeslot_pk} already exists."
                )
            else:
                raise e

    def update(self, instance: NotificationProfile, validated_data: dict):
        new_timeslot = validated_data.pop("timeslot")
        old_timeslot = instance.timeslot
        if new_timeslot != old_timeslot:
            # Save the notification profile with the new timeslot (will duplicate the object with a different PK)
            instance.timeslot = new_timeslot
            instance.save()
            # Delete the duplicate (old) object
            NotificationProfile.objects.get(timeslot=old_timeslot).delete()

        return super().update(instance, validated_data)

    def validate(self, attrs: dict):
        if attrs["timeslot"].user != self.context["request"].user:
            raise serializers.ValidationError("The user of 'timeslot' must be the same as the requesting user.")
        return attrs
