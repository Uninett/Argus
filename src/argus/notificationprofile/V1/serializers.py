from typing import List

from rest_framework import fields, serializers

from ..models import DestinationConfig, NotificationProfile
from ..serializers import FilterSerializer, TimeslotSerializer


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
        destination = profile.destinations.filter(media_id="sms").order_by("pk").first()
        if destination:
            return {
                "pk": destination.pk,
                "user": destination.user.pk,
                "phone_number": destination.settings["phone_number"],
            }
        return None


class RequestNotificationProfileSerializerV1(serializers.ModelSerializer):
    media = fields.MultipleChoiceField(choices=(("EM", "Email"), ("SM", "SMS")), default=["EM"])
    phone_number = fields.IntegerField(allow_null=True, required=False)

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
            sms_destination = user.destinations.filter(media_id="sms").filter(pk=phone_number).first()
            if not sms_destination:
                raise serializers.ValidationError(
                    {"phone_number": [f'Invalid pk "{phone_number}" - object does not exist.']}
                )
            destinations.append(sms_destination)
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

        # Update media to be empty
        if media == set():
            instance.destinations.set([])

        # Update media to not be empty
        if "SM" in media or "EM" in media:
            if "SM" in media and "EM" not in media:
                email_destinations = instance.destinations.filter(media_id="email")
                instance.destinations.remove(*email_destinations)

            if "EM" in media:
                if not instance.user.email and not instance.destinations.filter(media_id="email").exists():
                    raise serializers.ValidationError(
                        {"media": ["User email is not set, therefore this field cannot include email."]}
                    )
                if "SM" not in media:
                    sms_destinations = instance.destinations.filter(media_id="sms")
                    instance.destinations.remove(*sms_destinations)
                if instance.user.email:
                    default_email_destination = instance.user.destinations.filter(media_id="email").get(
                        settings__email_address=instance.user.email
                    )
                    if not default_email_destination in instance.destinations.all():
                        instance.destinations.add(default_email_destination)

        first_sms_destination = instance.destinations.filter(media_id="sms").order_by("pk").first()
        if (not phone_number == None) and ((not media and first_sms_destination) or "SM" in media):
            given_sms_destination = DestinationConfig.objects.filter(media_id="sms").filter(pk=phone_number).first()
            if not given_sms_destination:
                raise serializers.ValidationError(
                    {"phone_number": [f'Invalid pk "{phone_number}" - object does not exist.']}
                )
            if not first_sms_destination:
                instance.destinations.add(given_sms_destination)
            elif not first_sms_destination.pk == given_sms_destination.pk:
                instance.destinations.remove(first_sms_destination)
                instance.destinations.add(given_sms_destination)

        return super().update(instance, validated_data)

    def validate(self, attrs: dict):
        if attrs["timeslot"].user != self.context["request"].user:
            raise serializers.ValidationError("The user of 'timeslot' must be the same as the requesting user.")
        return attrs
