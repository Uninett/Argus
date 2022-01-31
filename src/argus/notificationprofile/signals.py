from argus.auth.models import User
from .models import DestinationConfig, Media, TimeRecurrence, Timeslot

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


# Create default DestinationConfig when a user is created
def create_default_destination_config(sender, instance: User, created, raw, *args, **kwargs):
    if raw or not created or not instance.email:
        return

    if instance.destination_configs.exists():
        email_destinations = instance.destination_configs.filter(media__slug="email")
        for destination in email_destinations:
            if destination.settings["synced"] and not destination.settings["email_address"] == instance.email:
                destination.settings["email_address"] = instance.email
                destination.save(update_fields=["settings"])
    else:
        DestinationConfig.objects.create(
            user=instance,
            media=Media.objects.get(slug="email"),
            settings={"email_address": instance.email},
        )


# Update default Destination if necessary when User logs in
def update_default_destination_config(sender, request, user, *args, **kwargs):
    if not user.email:
        return

    if user.destination_configs.exists():
        email_destinations = user.destination_configs.filter(media__slug="email")
        for destination in email_destinations:
            if destination.settings["synced"] and not destination.settings["email_address"] == user.email:
                destination.settings["email_address"] = user.email
                destination.save(update_fields=["settings"])
    else:
        DestinationConfig.objects.create(
            user=user,
            media=Media.objects.get(slug="email"),
            settings={"email_address": user.email},
        )
