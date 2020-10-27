from django.core.management.base import BaseCommand

from argus.auth.models import User


class Command(BaseCommand):
    help = "Turn superuser into user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="iReboke superuser powers from this user")

    def handle(self, *args, **options):
        username = options["username"]
        user = User.objects.get(username=username)
        self.stdout.write(f"Got user with id {user.id} for username {username}")
        user.is_staff = False
        user.is_superuser = False
        user.save()
