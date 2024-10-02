from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


User = get_user_model()


class Command(BaseCommand):
    help = "Turn user into superuser"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Turn this user into a superuser")

    def handle(self, *args, **options):
        username = options["username"]
        user = User.objects.get(username=username)
        self.stdout.write(f"Got user with id {user.id} for username {username}")
        user.is_staff = True
        user.is_superuser = True
        user.save()
