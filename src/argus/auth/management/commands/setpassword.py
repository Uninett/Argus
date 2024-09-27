from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


User = get_user_model()


class Command(BaseCommand):
    help = "Set password for a user, settable from script"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Set password for username")
        parser.add_argument("password", type=str, help="Set this password")

    def handle(self, *args, **options):
        user = User.objects.get(username=options["username"])
        user.set_password(options["password"])
        user.save()
