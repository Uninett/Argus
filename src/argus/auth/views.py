from django.contrib.auth import logout
from django.conf import settings
from django.db import transaction

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import BasicUserSerializer, EmptySerializer, RefreshTokenSerializer, UserSerializer
from .utils import get_authentication_backend_name_and_type


class ObtainNewAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        try:
            Token.objects.get(user=user).delete()
        except Token.DoesNotExist:
            pass
        token = Token.objects.create(user=user)
        return Response({"token": token.key})


class LogoutView(APIView):
    permission_classes = []

    @extend_schema(request=None, responses={"200": None})
    def post(self, request, *args, **kwargs):
        "Log out the logged in user"
        user = request.user
        if hasattr(user, "auth_token"):
            user_token = request.user.auth_token
            user_token.delete()
        # Log out from session
        logout(request)

        response = Response()
        response.delete_cookie(settings.ARGUS_TOKEN_COOKIE_NAME)
        return response


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(instance=request.user, context={"request": request})
        return Response(serializer.data)


class BasicUserDetail(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BasicUserSerializer
    queryset = User.objects.all()


class AuthMethodListView(APIView):
    http_method_names = ["get", "head", "options", "trace"]
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        data = get_authentication_backend_name_and_type(request=request)

        return Response(data)


@extend_schema_view(
    post=extend_schema(
        request=EmptySerializer,
    ),
)
class RefreshTokenView(APIView):
    http_method_names = ["post", "head", "options", "trace"]
    permission_classes = [IsAuthenticated]
    serializer_class = RefreshTokenSerializer
    write_serializer_class = EmptySerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            Token.objects.get(user=user).delete()
        except Token.DoesNotExist:
            raise ValidationError(
                f"No token for the user '{user}' exists, one needs to be created in the admin interface."
            )
        token = Token.objects.create(user=user)
        return Response({"token": token.key})
