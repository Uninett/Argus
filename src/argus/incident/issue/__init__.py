from __future__ import annotations

import importlib
import logging

from django.conf import settings

LOG = logging.getLogger(__name__)


__all__ = []

# Import issue class
def _import_class_from_dotted_path(dotted_path: str):
    module_name, class_name = dotted_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    class_ = getattr(module, class_name)
    return class_


ISSUE_PLUGIN = getattr(settings, "ISSUE_PLUGIN")
ISSUE_CLASS = None
if ISSUE_PLUGIN:
    ISSUE_CLASS = _import_class_from_dotted_path(ISSUE_PLUGIN)
ISSUE_ENDPOINT = getattr(settings, "ISSUE_ENDPOINT")
