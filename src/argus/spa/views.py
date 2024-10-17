from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from social_django import views as social_views

from .utils import get_authentication_backend_name_and_type


class AuthMethodSerializer(serializers.Serializer):
    type = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


@extend_schema_view(
    get=extend_schema(
        responses=AuthMethodSerializer,
    ),
)
class AuthMethodListView(APIView):
    http_method_names = ["get", "head", "options", "trace"]
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        data = get_authentication_backend_name_and_type(request=request)

        return Response(data)


def login_wrapper(request, backend, *args, **kwargs):
    # Needs to be called to fetch the user's Feide data (available through `social_auth`)
    _response = social_views.complete(request, backend, *args, **kwargs)

    user = request.user
    data = user.social_auth.first().extra_data

    if not user.get_full_name():
        # Update the full name of the user
        user.first_name = " ".join(data["fullname"].split()[:-1])
        user.last_name = data["fullname"].split()[-1]

        user.save()

    token, _created = Token.objects.get_or_create(user=user)
    response = redirect(settings.FRONTEND_URL, permanent=True)
    response.set_cookie(settings.ARGUS_SPA_TOKEN_COOKIE_NAME, token.key, domain=settings.SPA_COOKIE_DOMAIN)
    return response


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
        response.delete_cookie(settings.ARGUS_SPA_TOKEN_COOKIE_NAME)
        return response
