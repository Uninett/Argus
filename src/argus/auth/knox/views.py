import json

from rest_framework.authentication import BasicAuthentication
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import exceptions

from knox.views import LoginView as KnoxLoginView


class JsonAuthentication(BasicAuthentication):
    def authenticate(self, request):
        payload = json.loads(request.body)
        try:
            data = AuthTokenSerializer(payload, context={"request": request})
        except exceptions.ValidationError as e:
            raise exceptions.AuthenticationFailed(str(e)) from e
        return self.authenticate_credentials(data["username"], data["password"], request)


class LoginView(KnoxLoginView):
    authentication_classes = (JsonAuthentication, *KnoxLoginView.authentication_classes)
