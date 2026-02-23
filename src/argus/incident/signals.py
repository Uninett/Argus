from django.db.models import Q
from rest_framework.authtoken.models import Token

from argus.plannedmaintenance.utils import connect_incident_with_planned_maintenance_tasks
from .models import (
    Acknowledgement,
    Incident,
    SourceSystem,
    Tag,
    get_or_create_default_instances,
)


__all__ = [
    "delete_associated_user",
    "delete_associated_event",
    "close_token_incident",
]


def delete_associated_user(sender, instance: SourceSystem, *args, **kwargs):
    if hasattr(instance, "user") and instance.user:
        instance.user.delete()


def delete_associated_event(sender, instance: Acknowledgement, *args, **kwargs):
    if hasattr(instance, "event") and instance.event:
        instance.event.delete()


def close_token_incident(instance: Token, **kwargs):
    if not hasattr(instance.user, "source_system"):
        return

    open_expiry_incidents = Incident.objects.open().token_expiry()

    if not open_expiry_incidents:
        return

    argus_user, _, _ = get_or_create_default_instances()
    source_system_tag = Tag.objects.filter(
        (Q(key="source_system_id") & Q(value=instance.user.source_system.id))
    ).first()

    token_expiry_incident = open_expiry_incidents.filter(incident_tag_relations__tag=source_system_tag).first()

    if not token_expiry_incident:
        return

    token_expiry_incident.set_end(actor=argus_user)


def add_planned_maintenance_tasks_covering_incident(instance: Incident, **kwargs):
    connect_incident_with_planned_maintenance_tasks(incident=instance)
