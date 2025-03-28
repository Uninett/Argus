import importlib

from django.conf import settings
from django.utils.module_loading import import_string
from argus.htmx import defaults

FUNCTION_NAME_DEFAULT = "incident_list_filter"


def get_filter_function(arg=None):
    """Try and get the incident filter function from the ARGUS_HTMX_FILTER_FUNCTION setting.
    ARGUS_HTMX_FILTER_FUNCTION can be one of:

      * a callable that takes a Request and a QuerySet argument, and returns a Form and an updated
        QuerySet (see ``argus.htmx.incident.filter.incident_list_filter``)
      * a dotted path to an importable function that has the above signature
      * a dotted path to a module. This module should then contain a function named
        ``incident_list_filter`` with the above signature
    """
    if arg is None:
        arg = getattr(settings, "ARGUS_HTMX_FILTER_FUNCTION", defaults.ARGUS_HTMX_FILTER_FUNCTION)

    if callable(arg):
        return arg

    if isinstance(arg, str):
        try:
            # try importing the dotted path as a module. This will fail if the dotted path
            # points to a function instead
            module = importlib.import_module(arg)
        except ModuleNotFoundError:
            # import_string splits the dotted path into two sections (module, function name)
            # and tries to resolve that
            return import_string(arg)
        else:
            function = getattr(module, FUNCTION_NAME_DEFAULT, None)
            if function:
                return function
            raise ImportError(f"Could not import {FUNCTION_NAME_DEFAULT} from {arg}")

    raise TypeError("ARGUS_HTMX_FILTER_FUNCTION must be a callable or string")
