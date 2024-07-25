import importlib

from django.conf import settings


DEFAULT_BACKEND = "argus.filter.default"


def get_filter_backend():
    """Usage:

    filter_backend = get_filter_backend()
    """
    module_path = getattr(settings, "ARGUS_FILTER_BACKEND", DEFAULT_BACKEND)
    return importlib.import_module(module_path)
