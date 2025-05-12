from copy import deepcopy
from functools import cache
import logging
from typing import Mapping, Union

from django.conf import settings
from django.contrib.auth.backends import ModelBackend, RemoteUserBackend
from django.contrib import messages
from django.http import HttpRequest
from django.utils.module_loading import import_string

from argus.auth.models import Preferences, SessionPreferences

# importing is used to check for existence
# ruff: noqa: F401


__all__ = [
    "get_auth_backend_readiness",
    "get_authentication_backend_classes",
    "get_model_backend",
    "get_or_update_preference",
    "get_preference",
    "get_preference_obj",
    "get_psa_authentication_backends",
    "get_remote_user_backend",
    "has_allauth_socialaccount_backend",
    "has_psa_backend",
    "is_allauth_installed_correctly",
    "is_allauth_mfa_installed_correctly",
    "is_allauth_socialaccount_installed_correctly",
    "is_psa_installed_correctly",
    "pop_auth_backend",
    "save_preferences",
]


LOG = logging.getLogger(__name__)


@cache
def get_authentication_backend_classes():
    """Convert setting of strings to list of classes and cache

    Make a copy of the result if altering the list!
    """
    backend_dotted_paths = getattr(settings, "AUTHENTICATION_BACKENDS", [])
    backends = [import_string(path) for path in backend_dotted_paths]
    return backends


def pop_auth_backend(backends, backend):
    try:
        location = backends.index(backend)
    except ValueError:
        return None
    try:
        backend = backends.pop(location)
    except IndexError:
        return None
    return backend


def get_model_backend(backends):
    return pop_auth_backend(backends, ModelBackend)


def get_remote_user_backend(backends):
    return pop_auth_backend(backends, RemoteUserBackend)


# detect and set psa, allauth


@cache
def is_psa_installed_correctly():
    try:
        from social_core.backends.oauth import BaseOAuth2
    except ImportError:
        return False
    return "social_django" in settings.INSTALLED_APPS


@cache
def is_allauth_installed_correctly():
    try:
        import allauth
        from allauth import account
    except ImportError:
        return False
    if "allauth" not in settings.INSTALLED_APPS:
        return False
    return "allauth.account" in settings.INSTALLED_APPS


def is_allauth_mfa_installed_correctly():
    if not is_allauth_installed_correctly():
        return False
    try:
        from allauth import mfa
    except ImportError:
        return False
    return "allauth.mfa" in settings.INSTALLED_APPS


def is_allauth_socialaccount_installed_correctly():
    MAGIC_APP = "allauth.socialaccount.providers"
    if not is_allauth_installed_correctly():
        return False
    if "allauth.socialaccount" not in settings.INSTALLED_APPS:
        return False
    for app in settings.INSTALLED_APPS:
        if app.startswith(MAGIC_APP) and len(app) > len(MAGIC_APP):
            return True
    return False


def get_allauth_backend(backends):
    if not is_allauth_installed_correctly():
        return None
    try:
        from allauth.account.auth_backends import AuthenticationBackend
    except ImportError:
        return None
    return pop_auth_backend(backends, AuthenticationBackend)


def has_allauth_socialaccount_backend():
    if not is_allauth_socialaccount_installed_correctly():
        return False
    SOCIALACCOUNT_PROVIDERS = getattr(settings, "SOCIALACCOUNT_PROVIDERS", {})
    return bool(SOCIALACCOUNT_PROVIDERS)


def get_psa_authentication_backends(backends=None):
    if not is_psa_installed_correctly():
        return []
    backends = backends if backends else get_authentication_backend_classes()
    from social_core.backends.oauth import BaseOAuth2

    return [backend for backend in backends if issubclass(backend, BaseOAuth2)]


def has_psa_backend():
    return bool(get_psa_authentication_backends())


def get_auth_backend_readiness():
    backends = getattr(settings, "AUTHENTICATION_BACKENDS", [])
    backend_map = {
        "django-user": bool(get_model_backend(backends)),
        "remote-user": bool(get_remote_user_backend(backends)),
        "allauth": bool(get_allauth_backend(backends)),
        "allauth-social": has_allauth_socialaccount_backend(),
        "psa": has_psa_backend(),
    }
    return backend_map


# preferences


def get_preference_obj(request, namespace) -> Preferences:
    if namespace not in Preferences.NAMESPACES:
        raise ValueError(f"Unkown namespace '{namespace}'")
    if request.user.is_authenticated:
        prefs = request.user.get_namespaced_preferences(namespace)
    else:
        prefs = SessionPreferences(request.session, namespace)
    return prefs


def get_preference(request, namespace, preference):
    prefs = get_preference_obj(request, namespace)
    return prefs.get_preference(preference)


def save_preferences(request, data, namespace_or_prefs: Union[str, Preferences]):
    prefs = (
        namespace_or_prefs
        if isinstance(namespace_or_prefs, Preferences)
        else get_preference_obj(request, namespace_or_prefs)
    )
    saved = []
    failed = []
    for key in prefs.get_forms():
        if key in data:
            success = _save_preference(request, prefs, key, data)[1]
            if success:
                saved.append(key)
            else:
                failed.append(key)
    return saved, failed


def get_or_update_preference(request, data, namespace, preference):
    """Save the single preference given in data to the given namespace

    Returns a tuple (value, success). Value is the value of the preference, and success a boolean
    indicating whether the preference was successfully updated
    """
    prefs = get_preference_obj(request, namespace)
    return _save_preference(request, prefs, preference, data)


def _save_preference(request: HttpRequest, prefs: Preferences, preference: str, data: Mapping):
    value = prefs.get_preference(preference)
    LOG.debug("Changing %s: currently %s", preference, value)

    if data.get(preference, None) is None:
        LOG.debug("Failed to change %s, not in input: %s", preference, data)
        return value, False

    form = prefs.get_forms()[preference](data)

    if not form.is_valid():
        messages.warning(request, f"Failed to change {preference}, invalid input")
        LOG.warning("Failed to change %s, invalid input: %s", preference, data)
        return value, False

    old_value = deepcopy(value)  # Just in case value is mutable..
    value = form.cleaned_data[preference]
    if value == old_value:
        LOG.debug("Did not change %s: no change", preference)
        return value, True

    prefs.save_preference(preference, value)
    messages.success(request, f"Changed {preference}: {old_value} → {value}")
    LOG.info("Changed %s: %s → %s", preference, old_value, value)
    return value, True
