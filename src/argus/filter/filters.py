"""
Used for handling direct GET-queries in the API

Depends on django-filter
"""

from django import forms
from django_filters import rest_framework as filters

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from argus.notificationprofile.models import Filter, NotificationProfile
from argus.incident.fields import KeyValueField
from argus.incident.models import Incident


__all__ = [
    "INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS",
    "SOURCE_LOCKED_INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS",
    "IncidentFilter",
    "SourceLockedIncidentFilter",
]


# Used in OpenApiParameter
BooleanStringOAEnum = ("true", "false")


INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS = [
    OpenApiParameter(
        name="acked",
        description="Fetch acked (`true`) or unacked (`false`) incidents.",
        enum=BooleanStringOAEnum,
    ),
    OpenApiParameter(
        name="duration__gte",
        description="Fetch incidents with a duration longer of equal to `DURATION` minutes",
        type=int,
    ),
    OpenApiParameter(name="cursor", description="The pagination cursor value.", type=str),
    OpenApiParameter(
        name="end_time__gte",
        description="Fetch incidents that ended on or after `END_TIME`",
        type=OpenApiTypes.DATETIME,
    ),
    OpenApiParameter(
        name="end_time__isnull",
        description='Fetch incidents that have `end_time` set to None (`true`), a datetime or "infinity" (`false`).',
        enum=BooleanStringOAEnum,
    ),
    OpenApiParameter(
        name="end_time__lte",
        description="Fetch incidents that ended on or before `END_TIME`",
        type=OpenApiTypes.DATETIME,
    ),
    OpenApiParameter(
        name="filter_pk",
        description="Fetch incidents that are included in the filter with the given primary key.",
        type=int,
    ),
    OpenApiParameter(
        name="id__in",
        description="Fetch the incidents with an id in the given id list.",
    ),
    OpenApiParameter(name="level__lte", description="Fetch incidents with levels in `LEVEL`", enum=Incident.LEVELS),
    OpenApiParameter(
        name="notificationprofile_pk",
        description="Fetch incidents that are included in the filters connected to the notificationprofile with the given primary key.",
        type=int,
    ),
    OpenApiParameter(
        name="open",
        description="Fetch open (`true`) or closed (`false`) incidents.",
        enum=BooleanStringOAEnum,
    ),
    OpenApiParameter(
        name="source__id__in",
        description="Fetch incidents with a source with numeric id `ID1` or `ID2` or..",
    ),
    OpenApiParameter(
        name="source_incident_id",
        description="Fetch incidents with the specific source incident id.",
    ),
    OpenApiParameter(
        name="source__name__in",
        description="Fetch incidents with a source with name ``NAME1`` or ``NAME2`` or..",
    ),
    OpenApiParameter(
        name="source__type__in",
        description="Fetch incidents with a source of a type with numeric id `ID1` or `ID2` or..",
    ),
    OpenApiParameter(
        name="start_time__gte",
        description="Fetch incidents that started on or after `START_TIME`",
        type=OpenApiTypes.DATETIME,
    ),
    OpenApiParameter(
        name="start_time__lte",
        description="Fetch incidents that started on or before `START_TIME`",
        type=OpenApiTypes.DATETIME,
    ),
    OpenApiParameter(
        name="stateful",
        description="Fetch stateful (`true`) or stateless (`false`) incidents.",
        enum=BooleanStringOAEnum,
    ),
    OpenApiParameter(
        name="ticket",
        description="Fetch incidents with or without a ticket.",
        enum=BooleanStringOAEnum,
    ),
    OpenApiParameter(
        name="token_expiry",
        description="Fetch incidents that concern expiration of authentication tokens.",
        enum=BooleanStringOAEnum,
    ),
]
SOURCE_LOCKED_INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS = [
    OpenApiParameter(
        name="acked",
        description="Fetch acked (`true`) or unacked (`false`) incidents.",
        enum=BooleanStringOAEnum,
    ),
    OpenApiParameter(
        name="duration__gte",
        description="Fetch incidents with a duration longer of equal to `DURATION` minutes",
        type=int,
    ),
    OpenApiParameter(name="cursor", description="The pagination cursor value.", type=str),
    OpenApiParameter(
        name="end_time__gte",
        description="Fetch incidents that ended on or after `END_TIME`",
        type=OpenApiTypes.DATETIME,
    ),
    OpenApiParameter(
        name="end_time__isnull",
        description='Fetch incidents that have `end_time` set to None (`true`), a datetime or "infinity" (`false`).',
        enum=BooleanStringOAEnum,
    ),
    OpenApiParameter(
        name="end_time__lte",
        description="Fetch incidents that ended on or before `END_TIME`",
        type=OpenApiTypes.DATETIME,
    ),
    OpenApiParameter(
        name="filter_pk",
        description="Fetch incidents that are included in the filter with the given primary key.",
        type=int,
    ),
    OpenApiParameter(
        name="id__in",
        description="Fetch the incidents with an id in the given id list.",
    ),
    OpenApiParameter(
        name="notificationprofile_pk",
        description="Fetch incidents that are included in the filters connected to the notificationprofile with the given primary key.",
        type=int,
    ),
    OpenApiParameter(
        name="open",
        description="Fetch open (`true`) or closed (`false`) incidents.",
        enum=BooleanStringOAEnum,
    ),
    OpenApiParameter(
        name="source_incident_id",
        description="Fetch incidents with the specific source incident id.",
    ),
    OpenApiParameter(
        name="start_time__gte",
        description="Fetch incidents that started on or after `START_TIME`",
        type=OpenApiTypes.DATETIME,
    ),
    OpenApiParameter(
        name="start_time__lte",
        description="Fetch incidents that started on or before `START_TIME`",
        type=OpenApiTypes.DATETIME,
    ),
    OpenApiParameter(
        name="stateful",
        description="Fetch stateful (`true`) or stateless (`false`) incidents.",
        enum=BooleanStringOAEnum,
    ),
    OpenApiParameter(
        name="ticket",
        description="Fetch incidents with or without a ticket.",
        enum=BooleanStringOAEnum,
    ),
    OpenApiParameter(
        name="token_expiry",
        description="Fetch incidents that concern expiration of authentication tokens.",
        enum=BooleanStringOAEnum,
    ),
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
        from .queryset_filters import QuerySetFilter

        if name == "open":
            if value:
                return queryset.open()
            else:
                return queryset.closed()
        if name == "acked":
            if value:
                return queryset.acked()
            else:
                return queryset.not_acked()
        if name == "stateful":
            if value:
                return queryset.stateful()
            else:
                return queryset.stateless()
        if name == "tags":
            if value:
                if isinstance(value, str):
                    value = [value]
                return queryset.from_tags(*value)
        if name == "ticket":
            if value:
                return queryset.has_ticket()
            else:
                return queryset.lacks_ticket()
        if name == "duration__gte":
            if value:
                return queryset.is_longer_than_minutes(int(value))
        if name == "token_expiry":
            return queryset.token_expiry()
        if name == "filter_pk":
            return QuerySetFilter.incidents_by_filter_pk(queryset, value)
        if name == "notificationprofile_pk":
            return QuerySetFilter.incidents_by_notificationprofile_pk(queryset, value)
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
