from django.conf import settings
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.urls import reverse

from argus.auth.utils import (
    get_authentication_backend_classes,
    get_model_backend,
    get_psa_authentication_backends,
    get_remote_user_backend,
    pop_auth_backend,
)


REMOTE_USER_METHOD_NAME = getattr(settings, "ARGUS_REMOTE_USER_METHOD_NAME", "REMOTE_USER")
OIDC_METHOD_NAME = getattr(settings, "ARGUS_OIDC_METHOD_NAME", "OIDC")


def get_htmx_authentication_backend_name_and_type():
    """Needed for HTMX LoginView"""
    data = {}
    # use safetu copy
    backends = get_authentication_backend_classes()[:]

    if get_model_backend(backends):
        data["local"] = {
            "url": reverse("htmx:login"),
            "display_name": "Log In",
        }

    if get_remote_user_backend(backends):
        remote_user_data = {
            "url": "/",  # Should probably also be a setting
            "display_name": REMOTE_USER_METHOD_NAME,
        }
        data.setdefault("external", []).append(remote_user_data)

    # psa social auth
    for backend in get_psa_authentication_backends(backends):
        pop_auth_backend(backends, backend)
        display_name = backend.name
        if backend.name == "oidc":
            display_name = OIDC_METHOD_NAME
        psa_backend_data = {
            "url": reverse("social:begin", kwargs={"backend": backend.name}),
            "display_name": display_name,
        }
        data.setdefault("external", []).append(psa_backend_data)

    for backend in tuple(backends):
        pop_auth_backend(backends, backend)

    return data


class LoginView(DjangoLoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        backends = get_htmx_authentication_backend_name_and_type()
        context["backends"] = backends
        context["page_title"] = "Log in"
        return context
