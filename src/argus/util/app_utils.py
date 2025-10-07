from django.conf import settings
from django.apps import apps


def is_using_psa():
    turn_on_psa = getattr(settings, "USE_PYTHON_SOCIAL_AUTH", True)
    psa_is_installed = apps.is_installed("social_django")
    return turn_on_psa and psa_is_installed


def is_using_allauth():
    turn_on_psa = getattr(settings, "USE_PYTHON_SOCIAL_AUTH", True)
    allauth_is_installed = apps.is_installed("allauth")
    return allauth_is_installed and not turn_on_psa
