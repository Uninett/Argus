from rest_framework import serializers


class RefreshTokenSerializer(serializers.Serializer):
    token = serializers.CharField(label=("Token"), read_only=True)
