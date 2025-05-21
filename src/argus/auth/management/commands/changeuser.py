import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


User = get_user_model()


class Command(BaseCommand):
    help = "Change user"

    def add_arguments(self, parser):
        parser.add_argument(
            "username",
            type=str,
            help="Change user with this username",
        )
        parser.add_argument(
            "-p",
            "--password",
            type=str,
            help='Use this password for the user, otherwise also check the environment variable "DJANGO_USER_PASSWORD"',
        )
        parser.add_argument(
            "-e",
            "--email",
            type=str,
            help="Use this email address for the user",
        )
        parser.add_argument(
            "-f",
            "--first-name",
            type=str,
            help="First name of user",
        )
        parser.add_argument(
            "-l",
            "--last-name",
            type=str,
            help="Last name of user",
        )
        active = parser.add_mutually_exclusive_group()
        active.add_argument(
            "-a",
            "--activate",
            action="store_true",
            dest="active",
            default=None,
            help="Set the user to be active, allowed to log in",
        )
        active.add_argument(
            "-d",
            "--deactivate",
            action="store_true",
            dest="active",
            default=None,
            help="Deactivate the user, prevent log ins. This also unsets the password.",
        )
        # Setting staff is rarely needed. Could be used to prevent a superuser
        # from logging in to the admin but it would be better to revoke the
        # superuser or deactivate the user instead.
        staff = parser.add_mutually_exclusive_group()
        staff.add_argument(
            "--staff",
            action="store_true",
            dest="staff",
            default=None,
            help="Turn on staff-status, which gives access to the admin",
        )
        staff.add_argument(
            "--nostaff",
            action="store_false",
            dest="staff",
            default=None,
            help="Turn off staff-status, which prevents usage of the admin",
        )
        superuser = parser.add_mutually_exclusive_group()
        superuser.add_argument(
            "--superuser",
            action="store_true",
            dest="superuser",
            default=None,
            help="Make a user a superuser, also granting access to the admin",
        )
        superuser.add_argument(
            "--nosuperuser",
            action="store_false",
            dest="superuser",
            default=None,
            help="Revoke superuser status for a user, also preventing usage of the admin",
        )

    def handle(self, *args, **options):
        username = options["username"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'No user with the username "{username}" exists, did you mean the create a user?')

        changed_fields = set()

        password = options["password"] or os.environ.get("DJANGO_USER_PASSWORD", None)
        if password is not None:
            changed_fields.add("password")

        if options["superuser"] is not None:
            user.is_superuser = options["superuser"]
            changed_fields.add("is_superuser")
            user.is_staff = options["superuser"]
            changed_fields.add("is_staff")
        if options["staff"] is not None:
            user.is_staff = options["staff"]
            changed_fields.add("is_staff")
        if options["email"] is not None:
            user.email = options["email"]
            changed_fields.add("email")
        if options["first_name"] is not None:
            user.first_name = options["first_name"]
            changed_fields.add("first_name")
        if options["last_name"] is not None:
            user.last_name = options["last_name"]
            changed_fields.add("last_name")

        activation_msg = ""
        match options["active"]:
            case True:
                user.is_active = True
                changed_fields.add("is_active")
                activation_msg = "Activated user"
            case False:
                user.is_active = False
                changed_fields.add("is_active")
                user.set_unusable_password()
                changed_fields.add("password")
                activation_msg = "Deactivated user, unset the password"
            case _:
                activation_msg = ""

        user.save()
        self.stdout.write(self.style.SUCCESS(f'Successfully changed user "{username}"'))

        if password and user.is_active:
            user.set_password(options["password"])
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Password changed for user "{username}"'))
        if options["verbosity"] >= 1:
            self.stdout.write("Changed field(s): " + ", ".join(changed_fields))
            if activation_msg:
                self.stdout.write(activation_msg)
