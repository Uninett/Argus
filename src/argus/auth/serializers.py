from rest_framework import serializers

from .models import PhoneNumber, User


class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ["pk", "user", "phone_number"]


class UserSerializer(serializers.ModelSerializer):
    phone_numbers = PhoneNumberSerializer(many=True)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_numbers",
        ]


class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
        ]
