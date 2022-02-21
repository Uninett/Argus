from argus.auth.models import User
from .models import DestinationConfig, TimeRecurrence, Timeslot

__all__ = [
    "create_default_timeslot",
    "sync_email_destination_config",
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


# Sync user.email to DestinationConfig
def sync_email_destination_config(sender, instance: User, created, raw, *args, **kwargs):
    if raw or not instance.email:
        return

    email_destinations = instance.destination_configs.filter(media_id="email")
    found_synced_address = None
    changed_destinations = []
    for destination in email_destinations:
        settings = destination.settings.copy()
        if settings["email_address"] == instance.email:
            found_synced_address = True
            settings["synced"] = True
        else:
            settings["synced"] = False
        if settings != destination.settings:
            destination.settings = settings
            changed_destinations.append(destination)
    if not found_synced_address:  # Add new DestinationConfig
        new_destination = DestinationConfig(
            user=instance,
            media_id="email",
            settings={"email_address": instance.email, "synced": True},
        )
        # Triggers no signals
        DestinationConfig.objects.bulk_create([new_destination])
    if changed_destinations:  # Single query, triggers no signals
        DestinationConfig.objects.bulk_update(changed_destinations)
