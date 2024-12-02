import importlib

from django.conf import settings
from django.utils.module_loading import import_string

FUNCTION_NAME = "incident_list_filter"
DEFAULT_MODULE = "argus.htmx.incidents.filter"


def get_filter_function():
    """Try and get the incident filter function from the ARGUS_HTMX_FILTER_FUNCTION setting.
    ARGUS_HTMX_FILTER_FUNCTION can be one of:

      * a callable that takes a Request and a QuerySet argument, and returns a Form and an updated
        QuerySet (see ``argus.htmx.incidents.filter.incident_list_filter``)
      * a dotted path to an importable function that has the above signature
      * a dotted path to a module. This module should then contain a function named
        ``incident_list_filter`` with the above signature
    """
    setting = getattr(settings, "ARGUS_HTMX_FILTER_FUNCTION", DEFAULT_MODULE)

    if callable(setting):
        return setting

    if isinstance(setting, str):
        try:
            # try importing the dotted path as a module. This will fail if the dotted path
            # points to a function instead
            module = importlib.import_module(setting)
        except ModuleNotFoundError:
            # import_string splits the dotted path into two sections (module, function name)
            # and tries to resolve that
            return import_string(setting)
        else:
            function = getattr(module, FUNCTION_NAME, None)
            if function:
                return function
            raise ImportError(f"Could not import {FUNCTION_NAME} from {setting}")

    raise TypeError(f"ARGUS_HTMX_FILTER_FUNCTION must be a callable or string")
