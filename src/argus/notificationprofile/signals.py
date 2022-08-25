from argus.auth.models import User
from .models import DestinationConfig, TimeRecurrence, Timeslot

__all__ = [
    "create_default_timeslot",
    "sync_email_destination",
]


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

    email_destinations = instance.destinations.filter(media_id="email")
    synced_email_destination = email_destinations.filter(settings__synced=True).first()
    user_email_destination = email_destinations.filter(settings__email_address=instance.email).first()

    if not instance.email and not synced_email_destination:
        return

    if not instance.email and synced_email_destination:
        synced_email_destination.delete()
        return

    # There exists a destination with email_address == user.email
    if user_email_destination:
        if not user_email_destination == synced_email_destination:
            if synced_email_destination:
                synced_email_destination.settings["synced"] = False
                DestinationConfig.objects.bulk_update(objs=[synced_email_destination], fields=["settings"])
            user_email_destination.settings["synced"] = True
            DestinationConfig.objects.bulk_update(objs=[user_email_destination], fields=["settings"])

    # We need to create a destination with email_address=user.email
    else:
        if synced_email_destination:
            synced_email_destination.settings["synced"] = False
            DestinationConfig.objects.bulk_update(objs=[synced_email_destination], fields=["settings"])
        new_synced_destination = DestinationConfig(
            user=instance,
            media_id="email",
            settings={"email_address": instance.email, "synced": True},
        )
        DestinationConfig.objects.bulk_create([new_synced_destination])
