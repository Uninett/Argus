from rest_framework import serializers

from ..models import User


class RequestPhoneNumberSerializerV1(serializers.Serializer):
    phone_number = serializers.CharField()


class ResponsePhoneNumberSerializerV1(serializers.Serializer):
    pk = serializers.IntegerField()
    user = serializers.IntegerField()
    phone_number = serializers.CharField()


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

    def get_phone_numbers(self, user: User):
        return [
            {"pk": destination.pk, "user": user.pk, "phone_number": destination.settings["phone_number"]}
            for destination in user.destination_configs.filter(media__slug="sms")
        ]
