import json

from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import exceptions

from knox.views import LoginView as KnoxLoginView


class JsonAuthentication:
    def authenticate(self, request):
        payload = json.loads(request.body)
        try:
            serializer = AuthTokenSerializer(payload, context={"request": request})
            serializer.is_valid()
        except exceptions.ValidationError as e:
            raise exceptions.AuthenticationFailed(str(e)) from e

        user = serializer.data["user"]
        if not user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted.")

        return (user, None)

    def authenticate_header(self, request):
        pass


class LoginView(KnoxLoginView):
    authentication_classes = (JsonAuthentication, *KnoxLoginView.authentication_classes)
