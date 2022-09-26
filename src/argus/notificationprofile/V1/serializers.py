from typing import List

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
    media = serializers.SerializerMethodField("get_media")
    phone_number = serializers.SerializerMethodField("get_phone_number")

    class Meta:
        model = NotificationProfile
        fields = [
            "pk",
            "timeslot",
            "filters",
            "media",
            "active",
            "phone_number",
        ]

    def get_media(self, profile: NotificationProfile) -> List[str]:
        media = []
        if profile.destinations.filter(media_id="email").exists():
            media.append("EM")
        if profile.destinations.filter(media_id="sms").exists():
            media.append("SM")
        return media

    def get_phone_number(self, profile: NotificationProfile) -> str:
        if profile.destinations.filter(media_id="sms").exists():
            return profile.destinations.filter(media_id="sms").order_by("pk").first().settings["phone_number"]
        return None


class RequestNotificationProfileSerializerV1(serializers.ModelSerializer):
    media = fields.MultipleChoiceField(choices=(("EM", "Email"), ("SM", "SMS")), default=["EM"])
    phone_number = PhoneNumberField(allow_null=True, required=False)

    class Meta:
        model = NotificationProfile
        fields = [
            "timeslot",
            "filters",
            "media",
            "active",
            "phone_number",
        ]

    def create(self, validated_data: dict):
        phone_number = validated_data.pop("phone_number", None)
        media = validated_data.pop("media")
        user = validated_data["user"]
        destinations = []
        if "SM" in media:
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
        if "EM" in media:
            if not user.email:
                raise serializers.ValidationError(
                    {"media": ["User email is not set, therefore this field cannot include email."]}
                )
            destinations.append(user.destinations.filter(media_id="email").get(settings__email_address=user.email))

        profile = super().create(validated_data)
        profile.destinations.set(destinations)
        return profile

    def update(self, instance: NotificationProfile, validated_data: dict):
        phone_number = validated_data.pop("phone_number", None)
        media = validated_data.pop("media", None)
        # Update phone number without updating media
        if phone_number and not media and instance.destinations.filter(media_id="sms").exists():
            first_sms_destination = instance.destinations.filter(media_id="sms").order_by("pk").first()
            if not first_sms_destination.settings["phone_number"] == phone_number.as_e164:
                _switch_phone_numbers(first_sms_destination, phone_number, instance)

        # Update media
        if media:
            if "SM" in media:
                if "EM" not in media:
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
            if "EM" in media:
                if "SM" not in media:
                    sms_destinations = instance.destinations.filter(media_id="sms")
                    instance.destinations.remove(*sms_destinations)
                if not instance.user.email and not instance.destinations.filter(media_id="email").exists():
                    raise serializers.ValidationError(
                        {"media": ["User email is not set, therefore this field cannot include email."]}
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
