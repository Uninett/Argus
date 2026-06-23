from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

from argus.notificationprofile.media import send_notifications_to_users
from argus.notificationprofile.media import sync_media
from argus.notificationprofile.tasks import task_check_for_notifications
from argus.plannedmaintenance.utils import event_covered_by_planned_maintenance

from .models import DestinationConfig, TimeRecurrence, Timeslot

if TYPE_CHECKING:
    from argus.incident.models import Event


LOG = logging.getLogger(__name__)
User = get_user_model()

__all__ = [
    "trigger_sync_media",
    "create_default_timeslot",
    "sync_email_destination",
    "task_send_notification",
    "task_background_send_notification",
]


def trigger_sync_media(sender, **kwargs):
    sync_media()


# Create default immediate Timeslot when a user is created
def create_default_timeslot(sender, instance: User, created, raw, *args, **kwargs):
    if raw or not created or instance.timeslots.exists():
        return

    TimeRecurrence.objects.create(
        timeslot=Timeslot.objects.create(user=instance, name="All the time"),
        days=[day for day in TimeRecurrence.Day.values],
        start=TimeRecurrence.DAY_START,
        end=TimeRecurrence.DAY_END,
    )


def sync_email_destination(sender, instance: User, created, raw, *args, **kwargs):
    """
    Sync user.email to DestinationConfig
    """
    if raw:
        return

    email_address = instance.email
    email_destinations = instance.destinations.filter(media_id="email")
    # Because the user table only has a single email address this should be safe
    synced_email_destination = email_destinations.filter(managed=True).distinct().first()

    if not email_address:
        # Nothing to sync
        if not synced_email_destination:
            return

        # The address no longer needs to be synced
        synced_email_destination.delete()
        return

    # More likelihood of duplicates here
    user_email_destination = email_destinations.filter(settings__email_address=email_address).first()

    # There exists a destination with email_address == user.email
    if user_email_destination:
        if user_email_destination != synced_email_destination:
            if synced_email_destination:
                synced_email_destination.managed = False
                DestinationConfig.objects.bulk_update(objs=[synced_email_destination], fields=["managed"])
            user_email_destination.managed = True
            DestinationConfig.objects.bulk_update(objs=[user_email_destination], fields=["managed"])
        return

    # We need to create a destination with email_address=user.email
    if synced_email_destination:
        synced_email_destination.managed = False
        DestinationConfig.objects.bulk_update(objs=[synced_email_destination], fields=["managed"])
    new_synced_destination = DestinationConfig(
        user=instance,
        media_id="email",
        settings={"email_address": email_address},
        managed=True,
    )
    DestinationConfig.objects.bulk_create([new_synced_destination])


def task_send_notification(sender, instance: Event, *args, **kwargs):
    if event_covered_by_planned_maintenance(event=instance):
        return
    send_notifications_to_users(instance)


def task_background_send_notification(sender, instance: Event, *args, **kwargs):
    if event_covered_by_planned_maintenance(event=instance):
        return
    task_check_for_notifications.enqueue(instance.id)
