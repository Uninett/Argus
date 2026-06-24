from django.core.management.base import BaseCommand

from argus.notificationprofile.models import NotificationProfile


class Command(BaseCommand):
    help = "Toggle notification profile activation"

    def add_arguments(self, parser):
        parser.add_argument(
            "ids", type=int, nargs="+", help="Toggle activation of the notification profile with the given ids"
        )

    def handle(self, *args, **options):
        profile_ids = options["ids"]

        profiles = NotificationProfile.objects.filter(id__in=profile_ids)

        if not profiles:
            self.stderr.write(self.style.WARNING("No profiles with the given ids could be found."))
            return

        if profiles.count() < len(profile_ids):
            found_profile_ids = set([profile.pk for profile in profiles])
            missing_profile_ids = set(profile_ids) - found_profile_ids
            self.stderr.write(
                self.style.WARNING(
                    f"Profiles with the ids {missing_profile_ids} could not be found. Toggling activation of the remaining found profiles with the ids {found_profile_ids}."
                )
            )

        for profile in profiles:
            profile.active = not profile.active

        NotificationProfile.objects.bulk_update(objs=profiles, fields=["active"])
