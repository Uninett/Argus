import secrets
import string

from django.core.management.base import BaseCommand

from argus.auth.models import User
from argus.incident.models import get_or_create_default_instances


def generate_password_string(length=16):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(length))


class Command(BaseCommand):
    help = "Create standard instances, fill any lookup tables"

    def add_arguments(self, parser):
        parser.add_argument("-e", "--email", type=str, help="Set email for admin. Default: not set")
        parser.add_argument("-p", "--password", type=str, help="Set admin password. Default: long random string")
        parser.add_argument("-u", "--username", type=str, help="Set admin username. Default: admin")

    def handle(self, *args, **options):
        # Create source for argus, also creates a user
        get_or_create_default_instances()
        self.stdout.write('Ensured the existence of the source, source type and user "argus"')

        # Create default superuser
        email = options.get("email") or ""
        options_password = options.get("password", None)
        password = options_password or generate_password_string()
        options_username = options.get("username", None)
        username = options_username or "admin"
        first_name = username.capitalize()

        try:
            admin = User.objects.get(username=username)
        except User.DoesNotExist:
            admin = User.objects.create_superuser(
                username=username, email=email, first_name=first_name, last_name="", password=password
            )
            if options_password:
                msg = f'Successfully created Argus superuser "{admin.username}" with the chosen password'
            else:
                msg = (
                    "******************************************************************************\n\n"
                    f'  Created Argus superuser "{admin.username}" with password "{password}".\n\n'
                    "   Please change the password via the admin interface.\n\n"
                    "******************************************************************************"
                )
            self.stdout.write(self.style.SUCCESS(msg))
        else:
            msg = f"Argus superuser {username} already exists!"
            self.stderr.write(self.style.WARNING(msg))
