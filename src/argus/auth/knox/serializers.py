from rest_framework import serializers

from knox.settings import knox_settings


UserSerializer = knox_settings.USER_SERIALIZER
_expiry_datetime_format = knox_settings.EXPIRY_DATETIME_FORMAT


class BaseKnoxLoginResponseSerializer(serializers.Serializer):
    expiry = serializers.DateTimeField(format=_expiry_datetime_format)
    token = serializers.CharField()


if UserSerializer:

    class KnoxLoginResponseSerializer(BaseKnoxLoginResponseSerializer):
        user = UserSerializer()
else:

    class KnoxLoginResponseSerializer(BaseKnoxLoginResponseSerializer):
        pass
