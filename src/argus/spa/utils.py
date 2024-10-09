from django.contrib.auth.backends import ModelBackend

from rest_framework.reverse import reverse
from social_core.backends.base import BaseAuth
from social_core.backends.oauth import BaseOAuth2

from argus.auth.utils import get_authentication_backend_classes


def get_authentication_backend_name_and_type(request):
    backends = get_authentication_backend_classes()
    data = []
    if ModelBackend in backends:
        data.append(
            {
                "type": "username_password",
                "url": reverse("v1:api-token-auth", request=request),
                "name": "user_pw",
            }
        )

    data.extend(
        {
            "type": "OAuth2",
            "url": reverse("social:begin", kwargs={"backend": backend.name}, request=request),
            "name": backend.name,
        }
        for backend in backends
        if issubclass(backend, BaseOAuth2)
    )

    return data
