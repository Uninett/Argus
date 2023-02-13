from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.utils.module_loading import import_string

from rest_framework.reverse import reverse
from social_core.backends.base import BaseAuth
from social_core.backends.oauth import BaseOAuth2


def get_authentication_backend_classes():
    backend_dotted_paths = getattr(settings, "AUTHENTICATION_BACKENDS")
    backends = [import_string(path) for path in backend_dotted_paths]
    return backends


def get_psa_authentication_names(backends=None):
    backends = backends if backends else get_authentication_backend_classes()
    psa_backends = set()
    for backend in backends:
        if issubclass(backend, BaseAuth):
            psa_backends.add(backend.name)
    return sorted(psa_backends)


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
