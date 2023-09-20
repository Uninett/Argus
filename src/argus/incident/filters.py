from django import forms
from django_filters import rest_framework as filters

from .fields import KeyValueField
from .models import Incident
from argus.notificationprofile.models import Filter, NotificationProfile


__all__ = [
    "IncidentFilter",
    "SourceLockedIncidentFilter",
]


class TagFilter(filters.Filter):
    field_class = KeyValueField


class TagInFilter(filters.BaseInFilter, TagFilter):
    pass


class IntegerFilter(filters.NumberFilter):
    field_class = forms.IntegerField


class IncidentFilter(filters.FilterSet):
    open = filters.BooleanFilter(label="Open", method="incident_filter")
    acked = filters.BooleanFilter(label="Acked", method="incident_filter")
    stateful = filters.BooleanFilter(label="Stateful", method="incident_filter")
    ticket = filters.BooleanFilter(label="Ticket", method="incident_filter")
    tags = TagInFilter(label="Tags", method="incident_filter")
    duration__gte = filters.NumberFilter(label="Duration", method="incident_filter")
    token_expiry = filters.BooleanFilter(label="Token expiry", method="incident_filter")
    filter_pk = IntegerFilter(label="Filter pk", method="incident_filter")
    notificationprofile_pk = IntegerFilter(label="Notificationprofile pk", method="incident_filter")

    @property
    def qs(self):
        """
        In case of filtering by filter pk or notificationprofile pk returns an empty
        queryset if the filter/profile belongs to a different user than the requesting
        user

        Otherwise returns the default queryset
        """
        queryset = super(IncidentFilter, self).qs

        filter_pk = self.data.get("filter_pk", None)

        if filter_pk:
            filtr = Filter.objects.filter(pk=filter_pk).first()

            if filtr and filtr.user != self.request.user:
                return queryset.none()

        notificationprofile_pk = self.data.get("notificationprofile_pk", None)

        if notificationprofile_pk:
            profile = NotificationProfile.objects.filter(pk=notificationprofile_pk).first()

            if profile and profile.user != self.request.user:
                return queryset.none()

        return queryset

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
        elif name == "token_expiry":
            return queryset.token_expiry()
        elif name == "filter_pk":
            return queryset.filter_pk(value)
        elif name == "notificationprofile_pk":
            return queryset.notificationprofile_pk(value)
        return queryset

    class Meta:
        model = Incident
        fields = {
            "id": ["in"],
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
