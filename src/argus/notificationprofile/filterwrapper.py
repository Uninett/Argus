from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from argus.filter import get_filter_backend


filter_backend = get_filter_backend()
FallbackFilterWrapper = filter_backend.FallbackFilterWrapper
PrecisionFilterWrapper = filter_backend.PrecisionFilterWrapper

if TYPE_CHECKING:
    from django.db.models import Model

    from argus.incident.models import Event, Incident

    FilterWrapper = filter_backend.FilterWrapper


__all__ = [
    "NotificationProfileFilterWrapper",
]


class NotificationProfileFilterWrapper(PrecisionFilterWrapper):
    filterwrapper = FallbackFilterWrapper

    def __init__(self, model: Model, filterwrapper: Optional[FilterWrapper] = None):
        self.model = model
        super().__init__(model.filters, filterwrapper)

    def incident_fits(self, incident: Incident) -> bool:
        if not self.model.active:
            return False
        is_selected_by_time = self.model.timeslot.timestamp_is_within_time_recurrences(incident.start_time)
        if not is_selected_by_time:
            return False
        return super().incident_fits(incident)

    def event_fits(self, event: Event) -> bool:
        if not self.model.active:
            return False
        return super().event_fits(event)
