from rest_framework import serializers
from typing import List

from argus.notificationprofile.models import DestinationConfig
from ..models import User


class RequestPhoneNumberSerializerV1(serializers.Serializer):
    phone_number = serializers.CharField()


class ResponsePhoneNumberSerializerV1(serializers.Serializer):
    pk = serializers.SerializerMethodField("get_pk")
    user = serializers.SerializerMethodField("get_user")
    phone_number = serializers.SerializerMethodField("get_phone_number")

    def get_pk(self, destination: DestinationConfig) -> int:
        return destination.pk

    def get_user(self, destination: DestinationConfig) -> int:
        return destination.user.pk

    def get_phone_number(self, destination: DestinationConfig) -> str:
        return destination.settings["phone_number"]


class UserSerializerV1(serializers.ModelSerializer):
    phone_numbers = serializers.SerializerMethodField("get_phone_numbers")

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_numbers",
        ]

    def get_phone_numbers(self, user: User) -> List[dict]:
        return [
            {"pk": destination.pk, "user": user.pk, "phone_number": destination.settings["phone_number"]}
            for destination in user.destinations.filter(media_id="sms")
        ]
