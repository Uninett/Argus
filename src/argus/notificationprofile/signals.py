from argus.auth.models import User
from .models import DestinationConfig, TimeRecurrence, Timeslot

__all__ = [
    "create_default_timeslot",
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


# Add synced flag to DestinationConfig settings before saving
def add_synced_flag(sender, instance: DestinationConfig, raw, *args, **kwargs):
    if raw:
        return
    if instance.media.slug == "email":
        if instance.settings["email_address"] == instance.user.email:
            instance.settings["synced"] = True
        else:
            instance.settings["synced"] = False
