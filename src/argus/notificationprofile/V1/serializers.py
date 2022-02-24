from typing import List

from django.db import IntegrityError
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import fields, serializers

from ..models import NotificationProfile
from ..serializers import FilterSerializer, RequestDestinationConfigSerializer, TimeslotSerializer


class ResponseNotificationProfileSerializerV1(serializers.ModelSerializer):
    timeslot = TimeslotSerializer()
    filters = FilterSerializer(many=True)
    media_v1 = serializers.SerializerMethodField("get_media_v1")
    phone_number = serializers.SerializerMethodField("get_phone_number")

    class Meta:
        model = NotificationProfile
        fields = [
            "pk",
            "timeslot",
            "filters",
            "media_v1",
            "active",
            "phone_number",
        ]
        # "pk" needs to be listed, as "timeslot" is the actual primary key
        read_only_fields = ["pk"]

    def get_media_v1(self, profile: NotificationProfile) -> List[str]:
        media_v1 = []
        if profile.destinations.filter(media__slug="email").exists():
            media_v1.append("EM")
        if profile.destinations.filter(media__slug="sms").exists():
            media_v1.append("SM")
        return media_v1

    def get_phone_number(self, profile: NotificationProfile) -> str:
        if profile.destinations.filter(media__slug="sms").exists():
            return profile.destinations.filter(media__slug="sms").order_by("pk").first().settings["phone_number"]
        return None


class RequestNotificationProfileSerializerV1(serializers.ModelSerializer):
    media_v1 = fields.MultipleChoiceField(choices=(("EM", "Email"), ("SM", "SMS")), default=["EM"])
    phone_number = PhoneNumberField(allow_null=True, required=False)

    class Meta:
        model = NotificationProfile
        fields = [
            "pk",
            "timeslot",
            "filters",
            "media_v1",
            "active",
            "phone_number",
        ]
        # "pk" needs to be listed, as "timeslot" is the actual primary key
        read_only_fields = ["pk"]

    def create(self, validated_data: dict):
        phone_number = validated_data.pop("phone_number")
        media_v1 = validated_data.pop("media_v1")
        user = validated_data["user"]
        destinations = []
        if "SM" in media_v1:
            if not phone_number:
                raise serializers.ValidationError({"phone_number": ["This field may not be null."]})
            sms_destination = (
                user.destinations.filter(media__slug="sms").filter(settings__phone_number=phone_number.as_e164).first()
            )
            if sms_destination:
                destinations.append(sms_destination)
            else:
                sms_serializer = RequestDestinationConfigSerializer(
                    data={"media": "sms", "settings": {"phone_number": phone_number.as_e164}}
                )
                if sms_serializer.is_valid():
                    sms_serializer.save(user=user)
                    destinations.append(sms_serializer.instance)
        if "EM" in media_v1:
            if not user.email:
                raise serializers.ValidationError(
                    {"media_v1": ["User email is not set, therefore this field cannot include email."]}
                )
            destinations.append(user.destinations.filter(media__slug="email").get(settings__email_address=user.email))

        try:
            profile = super().create(validated_data)
            profile.destinations.set(destinations)
            return profile

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

        phone_number = validated_data.pop("phone_number", None)
        media_v1 = validated_data.pop("media_v1", None)
        if media_v1:
            if "SM" in media_v1:
                sms_destination = instance.destinations.filter(media__slug="sms").first()
                if sms_destination:
                    if not sms_destination.settings["phone_number"] == phone_number.as_e164:
                        if not phone_number:
                            raise serializers.ValidationError({"phone_number": ["This field may not be null."]})
                        sms_destination.settings["phone_number"] = phone_number.as_e164
                        sms_destination.save(updated_fields=["settings"])
                else:
                    if not phone_number:
                        raise serializers.ValidationError({"phone_number": ["This field may not be null."]})
                    sms_serializer = RequestDestinationConfigSerializer(
                        data={"media": "sms", "settings": {"phone_number": phone_number.as_e164}}
                    )
                    if sms_serializer.is_valid():
                        sms_serializer.save(user=instance.user)
                        instance.destinations.add(sms_serializer.instance)
            if "EM" in media_v1:
                if not instance.user.email:
                    raise serializers.ValidationError(
                        {"media_v1": ["User email is not set, therefore this field cannot include email."]}
                    )
                if not instance.destinations.filter(media__slug="email").first():
                    instance.destinations.add(
                        instance.user.destinations.filter(media__slug="email")
                        .filter(settings__email_address=instance.user.email)
                        .first()
                    )
            if "SM" not in media_v1 and instance.destinations.filter(media__slug="sms").exists():
                sms_destinations = instance.destinations.filter(media__slug="sms")
                instance.destinations.remove(*sms_destinations)
            if "EM" not in media_v1 and instance.destinations.filter(media__slug="email").exists():
                email_destinations = instance.destinations.filter(media__slug="email")
                instance.destinations.remove(*email_destinations)
        if not phone_number:
            if instance.destinations.filter(media__slug="sms").exists():
                sms_destinations = instance.destinations.filter(media__slug="sms")
                instance.destinations.remove(*sms_destinations)

        return super().update(instance, validated_data)

    def validate(self, attrs: dict):
        if attrs["timeslot"].user != self.context["request"].user:
            raise serializers.ValidationError("The user of 'timeslot' must be the same as the requesting user.")
        return attrs
