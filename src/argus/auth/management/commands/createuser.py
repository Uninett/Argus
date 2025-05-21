import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


User = get_user_model()


class Command(BaseCommand):
    help = "Create user"

    def add_arguments(self, parser):
        parser.add_argument(
            "username",
            type=str,
            help="Create user with this username",
        )
        # The createsuperuser-command can use the environment variable
        # DJANGO_SUPERUSER_PASSWORD, let's steal that
        parser.add_argument(
            "-p",
            "--password",
            type=str,
            help='Use this password for the new user, falls back to the environment variable "DJANGO_USER_PASSWORD"',
        )
        parser.add_argument(
            "-e",
            "--email",
            type=str,
            default="",
            help="Use this email address for the user",
        )
        parser.add_argument(
            "-f",
            "--first-name",
            type=str,
            default="",
            help="First name of user",
        )
        parser.add_argument(
            "-l",
            "--last-name",
            type=str,
            default="",
            help="Last name of user",
        )
        parser.add_argument(
            "--is-active",
            action="store_true",
            help="The user is allowed to log in",
        )
        parser.add_argument(
            "--is-staff",
            action="store_true",
            help="User may use the admin",
        )
        parser.add_argument(
            "--is-superuser",
            action="store_true",
            help="User is superuser and may use the admin",
        )

    def handle(self, *args, **options):
        username = options["username"]
        if User.objects.filter(username=username).exists():
            raise CommandError(f'A user with the username "{username}" already exists, cannot create')

        if options["is_superuser"]:
            options["is_staff"] = True
        data = {
            "username": username,
            "email": options["email"],
            "first_name": options["first_name"],
            "last_name": options["last_name"],
            "is_staff": options["is_staff"],
            "is_active": options["is_active"],
            "is_superuser": options["is_superuser"],
        }

        user = User.objects.create(**data)
        self.stdout.write(self.style.SUCCESS(f'Successfully created user "{username}"'))

        password = os.environ.get("DJANGO_USER_PASSWORD", options["password"])
        if password := options["password"]:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Password set for new user "{username}"'))
