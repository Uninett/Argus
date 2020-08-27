from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExpiringTokenAuthentication(TokenAuthentication):
    EXPIRATION_DURATION = timedelta(days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS)

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        if token.created + self.EXPIRATION_DURATION < timezone.now():
            token.delete()
            raise AuthenticationFailed("Token has expired.")

        return user, token
