from typing import Optional

from rest_framework import serializers
from rest_framework.reverse import reverse


from .models import User


class UserSerializer(serializers.ModelSerializer):
    admin_url = serializers.SerializerMethodField(method_name="get_admin_url")

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "admin_url",
        ]

    def get_admin_url(self, user: User) -> Optional[str]:
        if self.context.get("request") and user.is_staff:
            return reverse("admin:index", request=self.context["request"])
        return None


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
