from django.db import IntegrityError
from rest_framework import fields, serializers

from argus.auth.serializers import PhoneNumberSerializer

from ..models import NotificationMedia, NotificationProfile
from ..serializers import (
    TimeslotSerializer,
    FilterSerializer,
)


class ResponseNotificationProfileSerializerV1(serializers.ModelSerializer):
    timeslot = TimeslotSerializer()
    filters = FilterSerializer(many=True)
    phone_number = PhoneNumberSerializer(allow_null=True, required=False)

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

    def to_representation(self, instance: NotificationProfile):
        profile_dict = super().to_representation(instance)
        media_v1 = []
        for media in profile_dict["media"]:
            if media in ("sms", "email"):
                media_v1.append(media[:2].upper())
            profile_dict["media"] = ",".join(media_v1)
        return profile_dict


class RequestNotificationProfileSerializerV1(serializers.ModelSerializer):
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

    def to_internal_value(self, data: dict):
        if data.get("media") == ["EM", "SM"] or data.get("media") == ["SM", "EM"]:
            data["media"] = ["email", "sms"]
        elif data.get("media") == ["EM"]:
            data["media"] = ["email"]
        elif data.get("media") == ["SM"]:
            data["media"] = ["sms"]

        return super().to_internal_value(data)
