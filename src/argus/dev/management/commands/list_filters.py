from django.contrib.auth.hashers import check_password
from django.core.management.base import BaseCommand

from argus.filter import get_filter_backend
from argus.notificationprofile.models import Filter

filter_backend = get_filter_backend()
FilterSerializer = filter_backend.FilterSerializer


class Command(BaseCommand):
    help = "List existing filters"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "-p",
            "--pk",
            type=int,
            help="Select one filter to show by pk",
        )
        group.add_argument(
            "-n",
            "--name",
            type=str,
            help="Select one filter to show by name",
        )

    def handle(self, *args, **options):
        pk = options.get("pk") or None
        name = options.get("name") or None

        filters = Filter.objects.all()

        if pk:
            filters = filters.filter(id=pk)
        if name:
            filters = filters.filter(name=name)

        serializer = FilterSerializer(filters, many=True)
        self.stdout.write(self.style.SUCCESS(str(serializer.data)))
