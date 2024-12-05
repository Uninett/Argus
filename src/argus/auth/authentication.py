from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class DeprecatedExpiringTokenAuthentication(TokenAuthentication):
    EXPIRATION_DURATION = timedelta(days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS)

    def authenticate_credentials(self, key):
        model = self.get_model()

        try:
            token = model.objects.select_related("user").get(key=key)
        except model.DoesNotExist:
            return None

        if not token.user.is_active:
            raise AuthenticationFailed("User inactive or deleted.")

        if token.created + self.EXPIRATION_DURATION < timezone.now():
            token.delete()
            raise AuthenticationFailed("Token has expired.")

        return token.user, token
