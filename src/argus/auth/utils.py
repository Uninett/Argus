from django.conf import settings
from django.contrib.auth.backends import ModelBackend, RemoteUserBackend
from django.utils.module_loading import import_string

from rest_framework.reverse import reverse

from social_core.backends.oauth import BaseOAuth2


_all__ = [
    "get_authentication_backend_classes",
    "has_model_backend",
    "has_remote_user_backend",
    "get_psa_authentication_backends",
    "get_authentication_backend_name_and_type",
]


def get_authentication_backend_classes():
    backend_dotted_paths = getattr(settings, "AUTHENTICATION_BACKENDS")
    backends = [import_string(path) for path in backend_dotted_paths]
    return backends


def has_model_backend(backends):
    return ModelBackend in backends


def has_remote_user_backend(backends):
    return RemoteUserBackend in backends


def get_psa_authentication_backends(backends=None):
    backends = backends if backends else get_authentication_backend_classes()
    return [backend for backend in backends if issubclass(backend, BaseOAuth2)]


def get_authentication_backend_name_and_type(request):
    # Needed for SPA /login-methods/ API endpoint
    backends = get_authentication_backend_classes()
    data = []
    if has_model_backend(backends):
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
        for backend in get_psa_authentication_backends(backends)
    )

    return data
