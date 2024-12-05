import json

from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import exceptions

from knox.views import LoginView as KnoxLoginView


class JsonAuthentication:
    def authenticate(self, request):
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError as e:
            raise exceptions.AuthenticationFailed(str(e)) from e

        try:
            serializer = AuthTokenSerializer(data=payload, context={"request": request})
            serializer.is_valid(raise_exception=True)
        except exceptions.ValidationError as e:
            raise exceptions.AuthenticationFailed(str(e)) from e

        user = serializer.validated_data["user"]
        if not user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted.")

        return (user, None)

    def authenticate_header(self, request):
        pass


class LoginView(KnoxLoginView):
    authentication_classes = (JsonAuthentication, *KnoxLoginView.authentication_classes)
