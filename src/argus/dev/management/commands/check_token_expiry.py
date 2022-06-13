from datetime import timedelta
from functools import reduce
from operator import and_

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from rest_framework.authtoken.models import Token

from argus.incident.models import create_token_expiry_incident, get_or_create_default_instances, Incident, Tag


class Command(BaseCommand):
    help = "Post incident if token is close to expiry"

    def add_arguments(self, parser):
        parser.add_argument(
            "-d", "--days", default=7, type=int, help="Post incident if token expires in less than <number> days"
        )

    def handle(self, *args, **options):
        expiration_duration = timedelta(days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS)
        remind_before = timedelta(days=options.get("days"))
        _, _, source_system = get_or_create_default_instances()

        for token in Token.objects.select_related("user", "user__source_system").all():
            if hasattr(token.user, "source_system"):
                expiry_date = token.created + expiration_duration
                running_out_soon = (expiry_date - remind_before) < timezone.now()
                if running_out_soon:
                    tags = Tag.objects.filter(
                        (Q(key="problem_type") & Q(value="token_expiry"))
                        | (Q(key="source_system") & Q(value=token.user.source_system))
                    )
                    if len(tags) < 2:
                        # Incident can't exists since the two related tags are not existing yet
                        incident_exists_already = False
                    else:
                        incident_exists_already = Incident.objects.open().filter(source_id=source_system.id)
                        for tag in tags:
                            incident_exists_already = incident_exists_already.filter(incident_tag_relations__tag=tag)
                    if not incident_exists_already:
                        create_token_expiry_incident(token, expiry_date)
