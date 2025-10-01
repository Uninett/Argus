from django.conf import settings
from django.urls import reverse

from social_core.backends.oauth import BaseOAuth2

from argus.auth.utils import get_authentication_backend_classes


__all__ = [
    "get_psa_authentication_backends",
]


OIDC_METHOD_NAME = getattr(settings, "ARGUS_OIDC_METHOD_NAME", "OIDC")


def get_psa_authentication_backends(backends=None):
    backends = backends if backends else get_authentication_backend_classes()
    return [backend for backend in backends if issubclass(backend, BaseOAuth2)]


def serialize_psa_authentication_backends(backends=None):
    data = []
    for backend in get_psa_authentication_backends(backends):
        display_name = backend.name
        if backend.name == "oidc":
            display_name = OIDC_METHOD_NAME
        psa_backend_data = {
            "url": reverse("social:begin", kwargs={"backend": backend.name}),
            "display_name": display_name,
        }
        data.append(psa_backend_data)
    return data
