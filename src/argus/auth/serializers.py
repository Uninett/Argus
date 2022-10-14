from rest_framework import exceptions, serializers
from rest_framework.authtoken.models import Token

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
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


class UsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "pk",
            "username",
        ]
        read_only_fields = ["pk", "username"]


class RefreshTokenSerializer(serializers.Serializer):
    token = serializers.CharField(label=("Token"), read_only=True)


class EmptySerializer(serializers.Serializer):
    pass
