from datetime import timedelta
from urllib.request import urlopen
import json
import jwt

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication, BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import User


class ExpiringTokenAuthentication(TokenAuthentication):
    EXPIRATION_DURATION = timedelta(days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS)

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        if token.created + self.EXPIRATION_DURATION < timezone.now():
            token.delete()
            raise AuthenticationFailed("Token has expired.")

        return user, token


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        try:
            raw_token = self.get_raw_jwt_token(request)
        except ValueError:
            return None
        try:
            validated_token = jwt.decode(
                jwt=raw_token,
                algorithms=["RS256", "RS384", "RS512"],
                key=self.get_public_key(),
                options={
                    "require": [
                        "exp",
                        "nbf",
                        "aud",
                        "iss",
                        "sub",
                    ]
                },
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )
        except jwt.exceptions.PyJWTError as e:
            raise AuthenticationFailed(f"Error validating JWT token: {e}")
        username = validated_token["sub"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise AuthenticationFailed(f"No user found for username {username}")

        return user, validated_token

    def get_public_key(self):
        response = urlopen(settings.JWK_ENDPOINT)
        jwks = json.loads(response.read())
        jwk = jwks["keys"][0]
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        return public_key

    def get_raw_jwt_token(self, request):
        """Raises ValueError if a jwt token could not be found"""
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            raise ValueError("No Authorization header found")
        try:
            scheme, token = auth_header.split()
        except ValueError as e:
            raise ValueError(f"Failed to parse Authorization header: {e}")
        if scheme != settings.JWT_AUTH_SCHEME:
            raise ValueError(f"Invalid Authorization scheme: {scheme}")
        return token
