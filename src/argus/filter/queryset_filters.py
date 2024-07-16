from argus.notificationprofile.models import Filter
from argus.notificationprofile.models import NotificationProfile


def incidents_by_filter_pk(incident_queryset, filter_pk):
    """
    Returns all incidents that are included in the filter with the given primary
    key

    If no filter with that pk exists it returns no incidents
    """
    filtr = Filter.objects.filter(pk=filter_pk).first()

    if not filtr:
        return incident_queryset.none()

    return filtr.filtered_incidents.all()


def incidents_by_notificationprofile_pk(incident_queryset, notificationprofile_pk):
    """
    Returns all incidents that are included in the filters connected to the profile
    with the given primary key
    """
    notification_profile = NotificationProfile.objects.filter(pk=notificationprofile_pk).first()

    if not notification_profile:
        return incident_queryset.none()

    filters = notification_profile.filters.all()

    filtered_incidents_pks = set()
    for filtr in filters:
        filtered_incidents_pks.update(filtr.filtered_incidents.values_list("pk", flat=True))

    return incident_queryset.filter(pk__in=filtered_incidents_pks)
