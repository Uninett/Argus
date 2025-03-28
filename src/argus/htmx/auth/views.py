from django.conf import settings
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.urls import reverse

from argus.auth.utils import (
    has_model_backend,
    has_remote_user_backend,
    get_psa_authentication_backends,
    get_authentication_backend_classes,
)


REMOTE_USER_METHOD_NAME = getattr(settings, "ARGUS_REMOTE_USER_METHOD_NAME", "REMOTE_USER")
OIDC_METHOD_NAME = getattr(settings, "ARGUS_OIDC_METHOD_NAME", "OIDC")


def get_htmx_authentication_backend_name_and_type():
    # Needed for HTMX LoginView
    backends = get_authentication_backend_classes()

    data = {}
    if has_model_backend(backends):
        data["local"] = {
            "url": reverse("htmx:login"),
            "display_name": "Log In",
        }

    if has_remote_user_backend(backends):
        remote_user_data = {
            "url": "/",  # Should probably also be a setting
            "display_name": REMOTE_USER_METHOD_NAME,
        }
        data.setdefault("external", []).append(remote_user_data)

    for backend in get_psa_authentication_backends(backends):
        display_name = backend.name
        if backend.name == "oidc":
            display_name = OIDC_METHOD_NAME
        psa_backend_data = {
            "url": reverse("social:begin", kwargs={"backend": backend.name}),
            "display_name": display_name,
        }
        data.setdefault("external", []).append(psa_backend_data)

    return data


class LoginView(DjangoLoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        backends = get_htmx_authentication_backend_name_and_type()
        context["backends"] = backends
        context["page_title"] = "Log in"
        return context
