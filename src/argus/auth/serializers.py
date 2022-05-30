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
    old_token = serializers.CharField(label=("Old token"), write_only=True)
    token = serializers.CharField(label=("Token"), read_only=True)

    def validate(self, attrs):
        user = self.authenticate_credentials(key=attrs.get("old_token"))
        attrs["user"] = user
        return attrs

    def authenticate_credentials(self, key):
        try:
            token = Token.objects.select_related("user").get(key=key)
        except Token.DoesNotExist:
            raise serializers.ValidationError("Incorrect token.", code="authorization")
        if not token.user.is_active:
            raise serializers.ValidationError("User inactive or deleted.", code="authorization")

        return token.user
