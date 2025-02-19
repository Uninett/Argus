from copy import deepcopy
import logging
from typing import Mapping, Union

from django.conf import settings
from django.contrib.auth.backends import ModelBackend, RemoteUserBackend
from django.contrib import messages
from django.http import HttpRequest
from django.utils.module_loading import import_string

from social_core.backends.oauth import BaseOAuth2

from argus.auth.models import Preferences, SessionPreferences


__all__ = [
    "get_authentication_backend_classes",
    "has_model_backend",
    "has_remote_user_backend",
    "get_psa_authentication_backends",
    "get_preference_obj",
    "get_preference",
    "get_or_update_preference",
    "save_preferences",
]


LOG = logging.getLogger(__name__)


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
