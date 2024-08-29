from django.core.management.base import BaseCommand

from argus.auth.models import User
from argus.filter import get_filter_backend
from argus.incident.models import Incident
from argus.notificationprofile.models import Filter

filter_backend = get_filter_backend()
QuerySetFilter = filter_backend.QuerySetFilter


class Command(BaseCommand):
    help = "Bulk ack/open/close/set ticket url for all incidents that match the given filter."

    def add_arguments(self, parser):
        parser.add_argument(
            "filter",
            type=str,
            help="Select the filter by either name or pk",
        )
        parser.add_argument(
            "username",
            type=str,
            help="Identify yourself with a username",
        )

        subparsers = parser.add_subparsers(
            help="Select the action that should be applied to the incidents matching the given filter",
            required=True,
            dest="action",
        )

        ack_parser = subparsers.add_parser(
            "ack",
            help="Acknowledge all incidents that match the given filter",
        )
        ack_parser.add_argument(
            "-e",
            "--expiration",
            type=str,
            help="Set a specific expiration timestamp for the acknowledgement",
        )
        ack_parser.add_argument(
            "-t",
            "--timestamp",
            type=str,
            help="Set a specific timestamp for the acknowledgement",
        )
        ack_parser.add_argument(
            "-d",
            "--description",
            type=str,
            help="Set a specific description for the acknowledgement",
        )

        close_parser = subparsers.add_parser(
            "close",
            help="Close all incidents that match the given filter",
        )
        close_parser.add_argument(
            "-t",
            "--timestamp",
            type=str,
            help="Set a specific timestamp for the closing event",
        )
        close_parser.add_argument(
            "-d",
            "--description",
            type=str,
            help="Set a specific description for the closing event",
        )

        reopen_parser = subparsers.add_parser(
            "reopen",
            help="Reopen all incidents that match the given filter",
        )
        reopen_parser.add_argument(
            "-t",
            "--timestamp",
            type=str,
            help="Set a specific timestamp for the reopening event",
        )
        reopen_parser.add_argument(
            "-d",
            "--description",
            type=str,
            help="Set a specific description for the reopening event",
        )

        ticket_url_parser = subparsers.add_parser(
            "ticket_url",
            help="Set a ticket_url for all incidents that match the given filter",
        )
        ticket_url_parser.add_argument(
            "-u",
            "--url",
            type=str,
            help="Set the ticket url",
        )

    def handle(self, *args, **options):
        filter_pk_or_name = options.get("filter")
        action = options.get("action")
        username = options.get("username")

        actor = User.objects.filter(username=username).first()
        if not actor:
            self.stderr.write(self.style.WARNING("No user with the given username could be found."))
            return

        filter = Filter.objects.filter(name=filter_pk_or_name).first()
        if not filter and filter_pk_or_name.isdigit():
            filter = Filter.objects.filter(id=int(filter_pk_or_name)).first()
        if not filter:
            self.stderr.write(self.style.WARNING("No filter with the given pk or name could be found."))
            return

        first_filtered_incidents = QuerySetFilter.filtered_incidents(filter.filter)
        incident_pks = [incident.pk for incident in first_filtered_incidents]
        if not incident_pks:
            self.stdout.write(self.style.WARNING("No incidents for the given filter could be found."))
            return

        incident_qs = Incident.objects.filter(pk__in=incident_pks)

        timestamp = options.get("timestamp") or None
        description = options.get("description") or ""

        if action == "ticket_url":
            url = options.get("url") or None
            if not url:
                self.stderr.write(self.style.WARNING("A ticket url is needed."))
                return

            incident_qs.update_ticket_url(
                actor=actor,
                url=url,
                timestamp=timestamp,
            )

        if action == "ack":
            expiration = options.get("expiration") or None

            incident_qs.create_acks(
                actor=actor,
                timestamp=timestamp,
                description=description,
                expiration=expiration,
            )

        if action == "close":
            incident_qs.close(
                actor=actor,
                timestamp=timestamp,
                description=description,
            )

        if action == "reopen":
            incident_qs.reopen(
                actor=actor,
                timestamp=timestamp,
                description=description,
            )
