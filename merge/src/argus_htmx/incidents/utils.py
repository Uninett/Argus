import importlib

from django.conf import settings

FUNCTION_NAME = "incident_list_filter"
DEFAULT_MODULE = "argus_htmx.incidents.filter"


def get_filter_function():
    dotted_path = getattr(settings, "ARGUS_HTMX_FILTER_FUNCTION", DEFAULT_MODULE)
    module = importlib.import_module(dotted_path)
    function = getattr(module, FUNCTION_NAME, None)
    if function:
        return function
    raise ImportError(f"Could not import {FUNCTION_NAME} from {dotted_path}")
