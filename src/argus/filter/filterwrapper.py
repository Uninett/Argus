from __future__ import annotations

from datetime import datetime, time
from functools import reduce
import logging
from operator import or_
from typing import TYPE_CHECKING, Dict, Optional

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from argus.auth.models import User

from .constants import DEPRECATED_FILTER_NAMES

if TYPE_CHECKING:
    from argus.incident.models import Event, Incident

TriState = Optional[bool]


LOG = logging.getLogger(__name__)


class FilterWrapper:
    TRINARY_FILTERS = ("open", "acked", "stateful")

    def __init__(self, filterblob):
        self.fallback_filter = getattr(settings, "ARGUS_FALLBACK_FILTER", {})
        self.filter = filterblob.copy()

    def _get_tristate(self, tristate):
        fallback_filter = self.fallback_filter.get(tristate, None)
        return self.filter.get(tristate, fallback_filter)

    def are_tristates_empty(self):
        for tristate in self.TRINARY_FILTERS:
            if self._get_tristate(tristate) is not None:
                return False
        return True

    def is_maxlevel_empty(self):
        fallback_filter = self.fallback_filter.get("maxlevel", None)
        return not self.filter.get("maxlevel", fallback_filter)

    def is_event_types_empty(self):
        fallback_filter = self.fallback_filter.get("event_types", None)
        return not self.filter.get("event_types", fallback_filter)

    def are_source_system_ids_empty(self):
        fallback_filter = self.fallback_filter.get("sourceSystemIds", None)
        return not self.filter.get("sourceSystemIds", fallback_filter)

    def are_tags_empty(self):
        fallback_filter = self.fallback_filter.get("tags", None)
        return not self.filter.get("tags", fallback_filter)

    @property
    def is_empty(self):
        return (
            self.are_source_system_ids_empty()
            and self.are_tags_empty()
            and self.are_tristates_empty()
            and self.is_maxlevel_empty()
            and self.is_event_types_empty()
        )

    def get_incident_tristate_checks(self, incident) -> Dict[str, TriState]:
        if self.are_tristates_empty():
            return {}
        fits_tristates = {}
        for tristate in self.TRINARY_FILTERS:
            filter_tristate = self._get_tristate(tristate)
            if filter_tristate is None:
                LOG.debug('Tristates: "%s" not in filter, ignoring', tristate)
                fits_tristates[tristate] = None
                continue
            incident_tristate = getattr(incident, tristate, None)
            LOG.debug('Tristates: "%s": filter = %s, incident = %s', tristate, filter_tristate, incident_tristate)
            fits_tristates[tristate] = filter_tristate == incident_tristate
        return fits_tristates

    def incident_fits_maxlevel(self, incident):
        if self.is_maxlevel_empty():
            return None
        fallback_filter = self.fallback_filter.get("maxlevel", None)
        return incident.level <= min(filter(None, (self.filter["maxlevel"], fallback_filter)))

    def event_fits(self, event):
        if self.is_event_types_empty():
            return True
        fallback_filter = self.fallback_filter.get("event_types", [])
        return event.type in self.filter.get("event_types", fallback_filter)
