from typing import List

from django.db import IntegrityError
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import fields, serializers

from ..models import NotificationProfile
from ..serializers import FilterSerializer, RequestDestinationConfigSerializer, TimeslotSerializer


def _switch_phone_numbers(first_sms_destination, new_phone_number, instance):
    current_sms_destination = (
        instance.user.destinations.filter(media_id="sms")
        .filter(settings__phone_number=new_phone_number.as_e164)
        .first()
    )
    old_phone_number = first_sms_destination.settings["phone_number"]
    # Set phone number to None to avoid unique together restriction
    first_sms_destination.settings["phone_number"] = None
    first_sms_destination.save(update_fields=["settings"])
    if current_sms_destination:
        current_sms_destination.settings["phone_number"] = old_phone_number
        current_sms_destination.save(update_fields=["settings"])
        instance.destinations.add(current_sms_destination)
    else:
        sms_serializer = RequestDestinationConfigSerializer(
            data={"media": "sms", "settings": {"phone_number": old_phone_number}}
        )
        if sms_serializer.is_valid():
            sms_serializer.save(user=instance.user)
            instance.destinations.add(sms_serializer.instance)
    first_sms_destination.settings["phone_number"] = new_phone_number.as_e164
    first_sms_destination.save(update_fields=["settings"])


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
        if profile.destinations.filter(media_id="email").exists():
            media_v1.append("EM")
        if profile.destinations.filter(media_id="sms").exists():
            media_v1.append("SM")
        return media_v1

    def get_phone_number(self, profile: NotificationProfile) -> str:
        if profile.destinations.filter(media_id="sms").exists():
            return profile.destinations.filter(media_id="sms").order_by("pk").first().settings["phone_number"]
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
        phone_number = validated_data.pop("phone_number", None)
        media_v1 = validated_data.pop("media_v1")
        user = validated_data["user"]
        destinations = []
        if "SM" in media_v1:
            if not phone_number:
                raise serializers.ValidationError({"phone_number": ["This field may not be null."]})
            sms_destination = (
                user.destinations.filter(media_id="sms").filter(settings__phone_number=phone_number.as_e164).first()
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
            destinations.append(user.destinations.filter(media_id="email").get(settings__email_address=user.email))

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
        # Update phone number without updating media_v1
        if phone_number and not media_v1 and instance.destinations.filter(media_id="sms").exists():
            first_sms_destination = instance.destinations.filter(media_id="sms").order_by("pk").first()
            if not first_sms_destination.settings["phone_number"] == phone_number.as_e164:
                _switch_phone_numbers(first_sms_destination, phone_number, instance)

        # Update media
        if media_v1:
            if "SM" in media_v1:
                if "EM" not in media_v1:
                    email_destinations = instance.destinations.filter(media_id="email")
                    instance.destinations.remove(*email_destinations)
                first_sms_destination = instance.destinations.filter(media_id="sms").order_by("pk").first()
                if first_sms_destination:
                    if phone_number and not first_sms_destination.settings["phone_number"] == phone_number.as_e164:
                        _switch_phone_numbers(first_sms_destination, phone_number, instance)
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
                if "SM" not in media_v1:
                    sms_destinations = instance.destinations.filter(media_id="sms")
                    instance.destinations.remove(*sms_destinations)
                if not instance.user.email and not instance.destinations.filter(media_id="email").exists():
                    raise serializers.ValidationError(
                        {"media_v1": ["User email is not set, therefore this field cannot include email."]}
                    )
                if instance.user.email:
                    default_email_destination = instance.user.destinations.filter(media_id="email").get(
                        settings__email_address=instance.user.email
                    )
                    if not default_email_destination in instance.destinations.all():
                        instance.destinations.add(default_email_destination)

        return super().update(instance, validated_data)

    def validate(self, attrs: dict):
        if attrs["timeslot"].user != self.context["request"].user:
            raise serializers.ValidationError("The user of 'timeslot' must be the same as the requesting user.")
        return attrs
