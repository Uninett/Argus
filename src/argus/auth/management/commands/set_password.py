from django.core.management.base import BaseCommand

from argus.auth.models import User


class Command(BaseCommand):
    help = "Set password"

    def add_arguments(self, parser):
        parser.add_argument('password', type=str, help="Set this password")
        parser.add_argument('-u', '--username', type=str, help="Set password for username")

    def handle(self, *args, **options):
        user = User.objects.get(username=options['username'])
        user.set_password(options['password'])
        user.save()
