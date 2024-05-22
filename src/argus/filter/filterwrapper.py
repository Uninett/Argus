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
from argus.compat import StrEnum

from .constants import DEPRECATED_FILTER_NAMES


if TYPE_CHECKING:
    from argus.incident.models import Event, Incident

TriState = Optional[bool]


LOG = logging.getLogger(__name__)


class FilterKey(StrEnum):
    OPEN = "open"
    ACKED = "acked"
    STATEFUL = "stateful"
    SOURCE_SYSTEM_IDS = "sourceSystemIds"
    TAGS = "tags"
    EVENT_TYPES = "event_types"
    MAXLEVEL = "maxlevel"


class FilterWrapper:
    TRINARY_FILTERS = (FilterKey.OPEN, FilterKey.ACKED, FilterKey.STATEFUL)
    LIST_FILTERS = (FilterKey.SOURCE_SYSTEM_IDS, FilterKey.TAGS, FilterKey.EVENT_TYPES)
    INT_FILTERS = (FilterKey.MAXLEVEL,)
    FILTER_KEYS = TRINARY_FILTERS + LIST_FILTERS + INT_FILTERS

    def __init__(self, filterblob):
        self.fallback_filter = getattr(settings, "ARGUS_FALLBACK_FILTER", {})
        self.filter = filterblob.copy()

    def _get_filter_value(self, key):
        fallback_filter = self.fallback_filter.get(key, None)
        return self.filter.get(key, fallback_filter)

    def _get_filter_value_and_ignored_status(self, key):
        filter_ = self._get_filter_value(key)
        if key in self.TRINARY_FILTERS:
            return filter_, filter_ is None
        return filter_, not filter_

    @property
    def is_empty(self):
        return all(self._get_filter_value_and_ignored_status(key)[1] for key in self.FILTER_KEYS)

    def get_incident_tristate_checks(self, incident) -> Dict[str, TriState]:
        if all(self._get_filter_value_and_ignored_status(key)[1] for key in self.TRINARY_FILTERS):
            return {}
        fits_tristates = {}
        for tristate in self.TRINARY_FILTERS:
            filter_tristate = self._get_filter_value(tristate)
            if filter_tristate is None:
                LOG.debug('Tristates: "%s" not in filter, ignoring', tristate)
                fits_tristates[tristate] = None
                continue
            incident_tristate = getattr(incident, tristate, None)
            LOG.debug('Tristates: "%s": filter = %s, incident = %s', tristate, filter_tristate, incident_tristate)
            fits_tristates[tristate] = filter_tristate == incident_tristate
        return fits_tristates

    def _incident_fits_maxlevel(self, incident: Incident):
        filter_, ignored = self._get_filter_value_and_ignored_status(FilterKey.MAXLEVEL)
        if ignored:
            return None
        return incident.level <= filter_

    def _incident_fits_source_system(self, incident: Incident):
        filter_, ignored = self._get_filter_value_and_ignored_status(FilterKey.SOURCE_SYSTEM_IDS)
        if ignored:
            return None
        return incident.source.id in filter_

    def _incident_fits_tags(self, incident: Incident):
        filter_, ignored = self._get_filter_value_and_ignored_status(FilterKey.TAGS)
        if ignored:
            return None
        tags = set(tag.representation for tag in incident.deprecated_tags)
        return tags.issuperset(filter_)

    # public

    def event_fits(self, event):
        filter_, ignored = self._get_filter_value_and_ignored_status(FilterKey.EVENT_TYPES)
        if ignored:
            return True
        return event.type in filter_

    def incident_fits(self, incident: Incident):
        if self.is_empty:
            return False  # Filter is empty!
        checks = {}
        checks["source"] = self._incident_fits_source_system(incident)
        checks["tags"] = self._incident_fits_tags(incident)
        checks["max_level"] = self._incident_fits_maxlevel(incident)
        tristate_checks = self.get_incident_tristate_checks(incident)
        checks.update(tristate_checks)

        any_failed = False in checks.values()
        if any_failed:
            LOG.debug("Filter: %s: MISS! checks: %r", self, checks)
        else:
            LOG.debug("Filter: %s: HIT!", self)
        return not any_failed
