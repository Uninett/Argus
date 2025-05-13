from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from rest_framework.authtoken.models import Token


def assemble_token_auth_kwarg(token_key: str):
    return {"HTTP_AUTHORIZATION": f"Token {token_key}"}


def expire_token(token: Token):
    # Subtract an extra second, just to be sure
    token.created -= timedelta(days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS, seconds=1)
    token.save()
