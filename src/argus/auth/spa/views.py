from django.db import transaction

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import EmptySerializer
from .serializers import RefreshTokenSerializer


@extend_schema_view(
    post=extend_schema(
        deprecated=True,
        description="This endpoint is replaced by /api/v2/auth/token/login/",
        request=EmptySerializer,
    ),
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


@extend_schema_view(
    post=extend_schema(
        deprecated=True,
        description="This endpoint is replaced by /api/v2/auth/token/login/. Logging in with an old token will generate and a new token.",
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
