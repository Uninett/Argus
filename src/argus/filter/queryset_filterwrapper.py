from __future__ import annotations

from functools import reduce
import logging
from operator import or_
from typing import TYPE_CHECKING, Optional


from argus.compat import StrEnum
from argus.notificationprofile.models import Filter, NotificationProfile

# This cannot be merged with the other filterwrapper module since it uses
# models directly. There would be import loops!


if TYPE_CHECKING:
    pass


LOG = logging.getLogger(__name__)


class IncidentQuerySetFilterWrapper:
    @classmethod
    def filtered_incidents(cls, incident_queryset, filterblob):
        filtered_by_source = cls._incidents_with_source_systems(incident_queryset, filterblob)
        filtered_by_tags = cls._incidents_with_tags(incident_queryset, filterblob)
        filtered_by_tristates = cls._incidents_fitting_tristates(incident_queryset, filterblob)
        filtered_by_maxlevel = cls._incidents_fitting_maxlevel(incident_queryset, filterblob)

        return filtered_by_source & filtered_by_tags & filtered_by_tristates & filtered_by_maxlevel

    @staticmethod
    def _incidents_with_source_systems(incident_queryset, filterblob):
        source_list = filterblob.get("sourceSystemIds", [])
        if source_list:
            return incident_queryset.filter(source__in=source_list).distinct()
        return incident_queryset.distinct()

    @staticmethod
    def _incidents_with_tags(incident_queryset, filterblob):
        tags_list = filterblob.get("tags", [])
        if tags_list:
            return incident_queryset.from_tags(*tags_list)
        return incident_queryset.distinct()

    @staticmethod
    def _incidents_fitting_tristates(incident_queryset, filterblob):
        filter_open = filterblob.get("open", None)
        filter_acked = filterblob.get("acked", None)
        filter_stateful = filterblob.get("stateful", None)

        if filter_open is True:
            incident_queryset = incident_queryset.open()
        if filter_open is False:
            incident_queryset = incident_queryset.closed()
        if filter_acked is True:
            incident_queryset = incident_queryset.acked()
        if filter_acked is False:
            incident_queryset = incident_queryset.not_acked()
        if filter_stateful is True:
            incident_queryset = incident_queryset.stateful()
        if filter_stateful is False:
            incident_queryset = incident_queryset.stateless()
        return incident_queryset.distinct()

    @staticmethod
    def _incidents_fitting_maxlevel(incident_queryset, filterblob):
        maxlevel = filterblob.get("maxlevel", None)
        if not maxlevel:
            return incident_queryset.distinct()
        return incident_queryset.filter(level__lte=maxlevel).distinct()

    @classmethod
    def incidents_by_filter(cls, incident_queryset, filter: Filter):
        "Returns all incidents that fits the filter"

        if not incident_queryset.exists():
            return incident_queryset.none()

        return cls.filtered_incidents(incident_queryset, filter.filter)

    @classmethod
    def incidents_by_filter_pk(cls, incident_queryset, filter_pk: int):
        """
        Returns all incidents that fits the filter with the given primary key

        If no filter with that pk exists it returns an empty incident queryset.
        """
        filter = Filter.objects.filter(pk=filter_pk).first()

        if not filter or filter.is_empty:
            return incident_queryset.none()

        return cls.incidents_by_filter(incident_queryset, filter)

    @classmethod
    def incidents_by_notificationprofile(cls, incident_queryset, notification_profile: NotificationProfile):
        """
        Returns all incidents that fits the filters connected to the profile
        """
        if not incident_queryset.exists():
            return incident_queryset.none()

        filters = notification_profile.filters.all()

        querysets = []
        for filtr in filters:
            querysets.append(cls.filtered_incidents(incident_queryset, filtr.filter))

        if querysets:
            return reduce(or_, querysets)
        return incident_queryset.none()

    @classmethod
    def incidents_by_notificationprofile_pk(cls, incident_queryset, notification_profile_pk: int):
        """
        Returns all incidents that fits the filters connected to the profile
        with the given primary key

        If no notification profile with that pk exists it returns an empty
        incident queryset.
        """
        notification_profile = NotificationProfile.objects.filter(pk=notification_profile_pk).first()

        if not notification_profile:
            return incident_queryset.none()

        return cls.incidents_by_notificationprofile(incident_queryset, notification_profile)
