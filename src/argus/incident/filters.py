from django_filters import rest_framework as filters

from .fields import KeyValueField
from .models import Incident


__all__ = [
    "IncidentFilter",
    "SourceLockedIncidentFilter",
]


class TagFilter(filters.Filter):
    field_class = KeyValueField


class TagInFilter(filters.BaseInFilter, TagFilter):
    pass


class IncidentFilter(filters.FilterSet):
    open = filters.BooleanFilter(label="Open", method="incident_filter")
    acked = filters.BooleanFilter(label="Acked", method="incident_filter")
    stateful = filters.BooleanFilter(label="Stateful", method="incident_filter")
    ticket = filters.BooleanFilter(label="Ticket", method="incident_filter")
    tags = TagInFilter(label="Tags", method="incident_filter")
    duration__gte = filters.NumberFilter(label="Duration", method="incident_filter")

    @classmethod
    def incident_filter(cls, queryset, name, value):
        if name == "open":
            if value:
                return queryset.open()
            else:
                return queryset.closed()
        elif name == "acked":
            if value:
                return queryset.acked()
            else:
                return queryset.not_acked()
        elif name == "stateful":
            if value:
                return queryset.stateful()
            else:
                return queryset.stateless()
        elif name == "tags":
            if value:
                if isinstance(value, str):
                    value = [value]
                return queryset.from_tags(*value)
        elif name == "ticket":
            if value:
                return queryset.has_ticket()
            else:
                return queryset.lacks_ticket()
        elif name == "duration__gte":
            if value:
                return queryset.is_longer_than_minutes(int(value))
        return queryset

    class Meta:
        model = Incident
        fields = {
            "source__id": ["in"],
            "source__name": ["in"],
            "source__type": ["in"],
            "level": ["lte"],
            "source_incident_id": ["exact"],
            "start_time": ["gte", "lte"],
            "end_time": ["gte", "lte", "isnull"],
        }


class SourceLockedIncidentFilter(IncidentFilter):
    class Meta:
        model = Incident
        fields = {
            "source_incident_id": ["exact"],
            "start_time": ["gte", "lte"],
            "end_time": ["gte", "lte", "isnull"],
        }
