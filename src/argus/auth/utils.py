from django.conf import settings
from django.utils.module_loading import import_string

from social_core.backends.base import BaseAuth


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
