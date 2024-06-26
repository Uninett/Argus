from __future__ import annotations

from datetime import datetime, time
from functools import reduce
import logging
from operator import or_
from typing import TYPE_CHECKING, Dict, Optional, Any, Tuple

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from argus.auth.models import User
from argus.compat import StrEnum


if TYPE_CHECKING:
    from argus.incident.models import Event, Incident

TriState = Optional[bool]
FilterBlobType = Dict[str, Any]  # Validator: drf serializer, depends on API version


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

    def __init__(self, filterblob: FilterBlobType):
        self.fallback_filter = getattr(settings, "ARGUS_FALLBACK_FILTER", {})
        self.filter = filterblob.copy()

    def _get_filter_value(self, key: str) -> Optional[Any]:
        fallback_filter = self.fallback_filter.get(key, None)
        return self.filter.get(key, fallback_filter)

    def _get_filter_value_and_ignored_status(self, key: str) -> Tuple[Optional[Any], bool]:
        filter_ = self._get_filter_value(key)
        if key in self.TRINARY_FILTERS:
            return filter_, filter_ is None
        return filter_, not filter_

    @property
    def is_empty(self) -> bool:
        return all(self._get_filter_value_and_ignored_status(key)[1] for key in self.FILTER_KEYS)

    def _incident_fits_maxlevel(self, incident: Incident) -> TriState:
        filter_, ignored = self._get_filter_value_and_ignored_status(FilterKey.MAXLEVEL)
        if ignored:
            return None
        return incident.level <= filter_

    def _incident_fits_source_system(self, incident: Incident) -> TriState:
        filter_, ignored = self._get_filter_value_and_ignored_status(FilterKey.SOURCE_SYSTEM_IDS)
        if ignored:
            return None
        return incident.source.id in filter_

    def _incident_fits_tags(self, incident: Incident) -> TriState:
        filter_, ignored = self._get_filter_value_and_ignored_status(FilterKey.TAGS)
        if ignored:
            return None
        tags = set(tag.representation for tag in incident.deprecated_tags)
        return tags.issuperset(filter_)

    def _incident_fits_tristate(self, incident: Incident, tristate: str) -> TriState:
        if tristate not in self.TRINARY_FILTERS:
            return None
        filter_, ignored = self._get_filter_value_and_ignored_status(tristate)
        if ignored:
            return None
        incident_tristate = getattr(incident, tristate, None)
        return incident_tristate is filter_

    # public

    def event_fits(self, event) -> bool:
        filter_, ignored = self._get_filter_value_and_ignored_status(FilterKey.EVENT_TYPES)
        if ignored:
            return True
        return event.type in filter_

    def incident_fits(self, incident: Incident) -> bool:
        if self.is_empty:
            return False  # Filter is empty!
        checks = {}
        checks["source"] = self._incident_fits_source_system(incident)
        checks["tags"] = self._incident_fits_tags(incident)
        checks["max_level"] = self._incident_fits_maxlevel(incident)
        for tristate in self.TRINARY_FILTERS:
            checks[tristate.value] = self._incident_fits_tristate(incident, tristate)

        any_failed = False in checks.values()
        if any_failed:
            LOG.debug("Filter: %s: MISS! checks: %r", self, checks)
        else:
            LOG.debug("Filter: %s: HIT!", self)
        return not any_failed


class ComplexFilterWrapper:
    def __init__(self, **kwargs):
        self.profile = kwargs.pop("profile", None)

    def incident_fits(self, incident: Incident) -> bool:
        if not self.profile.active:
            return False
        is_selected_by_time = self.profile.timeslot.timestamp_is_within_time_recurrences(incident.start_time)
        if not is_selected_by_time:
            return False
        for f in self.profile.filters.only("filter"):
            if not FilterWrapper(f.filter).incident_fits(incident):
                return False
        return True

    def event_fits(self, event: Event) -> bool:
        if not self.profile.active:
            return False
        # return as early as possible
        for f in self.profile.filters.only("filter"):
            if FilterWrapper(f.filter).event_fits(event):
                return True
        return False
