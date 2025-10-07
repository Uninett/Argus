from django.conf import settings
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.urls import reverse

from argus.auth.utils import (
    has_model_backend,
    has_remote_user_backend,
    get_authentication_backend_classes,
)
from argus.util.app_utils import is_using_allauth


REMOTE_USER_METHOD_NAME = getattr(settings, "ARGUS_REMOTE_USER_METHOD_NAME", "REMOTE_USER")


def get_htmx_authentication_backend_name_and_type():
    # Needed for HTMX LoginView
    backends = get_authentication_backend_classes()

    login_urlname = "account_login" if is_using_allauth() else "login"
    data = {}
    if has_model_backend(backends):
        data["local"] = {
            "url": reverse(login_urlname),
            "display_name": "Log In",
        }

    if has_remote_user_backend(backends):
        remote_user_data = {
            "url": "/",  # Should probably also be a setting
            "display_name": REMOTE_USER_METHOD_NAME,
        }
        data.setdefault("external", []).append(remote_user_data)
    return data


class LoginView(DjangoLoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        backends = get_htmx_authentication_backend_name_and_type()
        context["backends"] = backends
        context["page_title"] = "Log in"
        return context
