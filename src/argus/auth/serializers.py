from rest_framework import serializers

from .models import PhoneNumber, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ["pk", "user", "phone_number"]
