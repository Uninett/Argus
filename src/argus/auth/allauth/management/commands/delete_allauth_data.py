from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from allauth.socialaccount.models import SocialAccount


User = get_user_model()


class Command(BaseCommand):
    help = "Delete allauth data for users"

    def add_arguments(self, parser):
        users = parser.add_mutually_exclusive_group()
        users.add_argument(
            "--uid",
            type=int,
            nargs="*",
            help="Delete the allauth data for users with the listed uids",
        )
        users.add_argument(
            "--all",
            action="store_true",
            help="Delete allauth data for all users",
        )

    def handle(self, *args, **options):
        users = User.objects.exclude(socialaccount=None)
        if options["all"]:
            pass
        elif options["uid"]:
            users = users.filter(id__in=options["uid"])
        else:
            raise CommandError("No users to delete allauth data for")
        allauths = SocialAccount.objects.filter(user__in=users)
        count = allauths.count()
        if not count:
            self.stderr.write(self.style.WARNING("Nothing to delete"))
        else:
            deleted = allauths.delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted[0]} of {count}"))
