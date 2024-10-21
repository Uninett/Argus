from django.db import transaction

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    BasicUserSerializer,
    EmptySerializer,
    RefreshTokenSerializer,
    UserSerializer,
)


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
