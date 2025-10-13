from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from argus.auth.allauth.utils import convert_from_psa_socialaccount


User = get_user_model()


class Command(BaseCommand):
    help = "Convert python social auth data to allauth data"

    def add_arguments(self, parser):
        users = parser.add_mutually_exclusive_group()
        users.add_argument(
            "--uid",
            type=int,
            nargs="*",
            help="Convert the python social auth data for users with the listed uids",
        )
        users.add_argument(
            "--all",
            action="store_true",
            help="Convert python social auth data for all users",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete python social auth data",
        )

    def handle(self, *args, **options):
        if options["all"]:
            users = User.objects.all()
        elif options["uid"]:
            users = User.objects.filter(id__in=options["uid"])
        else:
            raise CommandError("No users to convert")
        for user in users:
            ok, skipped, bad_extra_data = convert_from_psa_socialaccount(user)
            if ok:
                ok = ", ".join(ok)
                self.stdout.write(self.style.SUCCESS(f'Successfully converted user "{user.username}, providers: {ok}"'))
            if skipped:
                skipped = ", ".join(skipped)
                self.stderr.write(
                    self.style.ERROR(f'User "{user.username}" already has data for provider(s): {skipped}')
                )
            if bad_extra_data:
                data = repr(bad_extra_data)
                self.stderr.write(
                    self.style.ERROR(
                        f'There are problems with the extra-data for user #{user.id} "{user.username}": {data}. The converter needs improving'
                    )
                )
