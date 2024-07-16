from functools import reduce
from operator import or_

from argus.incident.models import Incident
from argus.notificationprofile.models import Filter
from argus.notificationprofile.models import NotificationProfile


def incidents_by_filter(incident_queryset, filter: Filter):
    "Returns all incidents that are included in the filter instance"
    return filtered_incidents(filter, incident_queryset).all()


def incidents_by_filter_pk(incident_queryset, filter_pk: int):
    """
    Returns all incidents that are included in the filter with the given primary
    key

    If no filter with that pk exists it returns no incidents
    """
    filtr = Filter.objects.filter(pk=filter_pk).first()

    if not filtr:
        return incident_queryset.none()

    return incidents_by_filter(incident_queryset, filtr)


def incidents_by_notificationprofile(incident_queryset, notificationprofile):
    filters = notificationprofile.filters.all()

    filtered_incidents_pks = set()
    for filtr in filters:
        filtered_incidents_pks.update(filtered_incidents(filtr, incident_queryset).values_list("pk", flat=True))

    return incident_queryset.filter(pk__in=filtered_incidents_pks)


def incidents_by_notificationprofile_pk(incident_queryset, notificationprofile_pk):
    """
    Returns all incidents that are included in the filters connected to the profile
    with the given primary key
    """
    notification_profile = NotificationProfile.objects.filter(pk=notificationprofile_pk).first()

    if not notification_profile:
        return incident_queryset.none()

    return incidents_by_notificationprofile(incident_queryset, notification_profile)


def incidents_with_source_systems(self, incident_queryset, data=None):
    if not data:
        data = self.filter.copy()
    source_list = data.get("sourceSystemIds", [])
    if source_list:
        return incident_queryset.filter(source__in=source_list).distinct()
    return incident_queryset.distinct()


def incidents_with_tags(self, incident_queryset, data=None):
    if not data:
        data = self.filter.copy()
    tags_list = data.get("tags", [])
    if tags_list:
        return incident_queryset.from_tags(*tags_list)
    return incident_queryset.distinct()


def incidents_fitting_tristates(
    self,
    incident_queryset,
    data=None,
):
    if not data:
        data = self.filter.copy()
    fitting_incidents = incident_queryset
    filter_open = data.get("open", None)
    filter_acked = data.get("acked", None)
    filter_stateful = data.get("stateful", None)

    if filter_open is True:
        fitting_incidents = fitting_incidents.open()
    if filter_open is False:
        fitting_incidents = fitting_incidents.closed()
    if filter_acked is True:
        fitting_incidents = fitting_incidents.acked()
    if filter_acked is False:
        fitting_incidents = fitting_incidents.not_acked()
    if filter_stateful is True:
        fitting_incidents = fitting_incidents.stateful()
    if filter_stateful is False:
        fitting_incidents = fitting_incidents.stateless()
    return fitting_incidents.distinct()


def incidents_fitting_maxlevel(self, incident_queryset, data=None):
    if not data:
        data = self.filter.copy()
    maxlevel = data.get("maxlevel", None)
    if not maxlevel:
        return incident_queryset.distinct()
    return incident_queryset.filter(level__lte=maxlevel).distinct()


def filtered_incidents(filter: Filter, incident_queryset=None):
    if incident_queryset is None:
        incident_queryset = Incident.objects.all()
    if filter.is_empty:
        return Incident.objects.none().distinct()
    data = filter.filter.copy()
    filtered_by_source = incidents_with_source_systems(filter, incident_queryset, data=data)
    filtered_by_tags = incidents_with_tags(filter, incident_queryset, data=data)
    filtered_by_tristates = incidents_fitting_tristates(filter, incident_queryset, data=data)
    filtered_by_maxlevel = incidents_fitting_maxlevel(filter, incident_queryset, data=data)

    return filtered_by_source & filtered_by_tags & filtered_by_tristates & filtered_by_maxlevel


def np_filtered_incidents(notificationprofile: NotificationProfile):
    qs = [filtered_incidents(filter_) for filter_ in notificationprofile.filters.all()]
    return reduce(or_, qs)
