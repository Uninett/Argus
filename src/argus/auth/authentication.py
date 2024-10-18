from datetime import timedelta
from urllib.request import urlopen
from urllib.parse import urljoin
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
    REQUIRED_CLAIMS = ["exp", "nbf", "aud", "iss", "sub"]
    SUPPORTED_ALGORITHMS = ["RS256", "RS384", "RS512"]
    AUTH_SCHEME = "Bearer"

    def authenticate(self, request):
        try:
            raw_token = self.get_raw_token(request)
        except ValueError:
            return None
        validated_token = self.decode_token(raw_token)
        return self.get_user(validated_token), validated_token

    def get_public_key(self, kid):
        r = urlopen(self.get_jwk_endpoint())
        jwks = json.loads(r.read())
        for jwk in jwks.get("keys"):
            if jwk["kid"] == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        raise AuthenticationFailed(f"Invalid kid '{kid}'")

    def get_raw_token(self, request):
        """Raises ValueError if a jwt token could not be found"""
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            raise ValueError("No Authorization header found")
        try:
            scheme, token = auth_header.split()
        except ValueError as e:
            raise ValueError(f"Failed to parse Authorization header: {e}")
        if scheme != self.AUTH_SCHEME:
            raise ValueError(f"Invalid Authorization scheme '{scheme}'")
        return token

    def decode_token(self, raw_token):
        kid = self.get_kid(raw_token)
        try:
            validated_token = jwt.decode(
                jwt=raw_token,
                algorithms=self.SUPPORTED_ALGORITHMS,
                key=self.get_public_key(kid),
                options={"require": self.REQUIRED_CLAIMS},
                audience=settings.JWT_AUDIENCE,
                issuer=self.get_openid_issuer(),
            )
            return validated_token
        except jwt.exceptions.PyJWTError as e:
            raise AuthenticationFailed(f"Error validating token: {e}")

    def get_user(self, token):
        username = token["sub"]
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise AuthenticationFailed(f"No user found for username '{username}'")

    def get_openid_config(self):
        url = urljoin(settings.OIDC_ENDPOINT, ".well-known/openid-configuration")
        r = urlopen(url)
        return json.loads(r.read())

    def get_jwk_endpoint(self):
        openid_config = self.get_openid_config()
        return openid_config["jwks_uri"]

    def get_openid_issuer(self):
        openid_config = self.get_openid_config()
        return openid_config["issuer"]

    def get_kid(self, token):
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise AuthenticationFailed("Token must include the 'kid' header")
        return kid
