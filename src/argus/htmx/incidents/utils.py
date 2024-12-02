import importlib

from django.conf import settings

FUNCTION_NAME = "incident_list_filter"
DEFAULT_MODULE = "argus.htmx.incidents.filter"


def get_filter_function():
    setting = getattr(settings, "ARGUS_HTMX_FILTER_FUNCTION", DEFAULT_MODULE)
    if callable(setting):
        return setting
    if isinstance(setting, str):
        module = importlib.import_module(setting)
        function = getattr(module, FUNCTION_NAME, None)
        if function:
            return function
        raise ImportError(f"Could not import {FUNCTION_NAME} from {setting}")
    raise TypeError(f"ARGUS_HTMX_FILTER_FUNCTION must be a callable or string")
