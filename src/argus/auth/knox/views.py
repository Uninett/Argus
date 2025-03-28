import json

from rest_framework.authentication import BaseAuthentication
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework import exceptions
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, PolymorphicProxySerializer

from knox import views

from ..serializers import EmptySerializer
from . import serializers


class JsonAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if not request.body:
            # fallback to next authentication method
            return None

        # Because drf ApiRequestFactory does not spit out drf requests but
        # Django requests we have to do our own json-parsing. TESTING
        # SOMETIMES SUCK.
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


@extend_schema_view(
    post=extend_schema(
        request=PolymorphicProxySerializer(
            component_name="LoginData",
            serializers=[
                AuthTokenSerializer,
                EmptySerializer,
            ],
            # this is abuse of PolymorphicProxySerializer, must be set
            resource_type_field_name="random_string",
        ),
        responses={
            200: serializers.KnoxLoginResponseSerializer,
        },
    ),
)
class LoginView(views.LoginView):
    authentication_classes = (JsonAuthentication, *views.LoginView.authentication_classes)
    login_required = False


@extend_schema_view(
    post=extend_schema(
        responses={
            204: OpenApiResponse(response=None),
        },
    ),
)
class LogoutView(views.LogoutView):
    pass


@extend_schema_view(
    post=extend_schema(
        responses={
            204: OpenApiResponse(response=None),
        },
    ),
)
class LogoutAllView(views.LogoutAllView):
    pass
