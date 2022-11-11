from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from rest_framework.authtoken.models import Token

from argus.incident.models import (
    create_token_expiry_incident,
    get_or_create_default_instances,
    Incident,
    Tag,
)


def find_expiring_tokens(number_of_days):
    """
    Returns all tokens that are expired or will expire within the next given
    number of days

    This function should actually be a part of the Token model or manager
    class, but since these aren't supplied by Argus, it is kept here for now
    """
    expiration_duration = timedelta(days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS)
    remind_before = timedelta(days=number_of_days)
    expiring_tokens = []

    for token in (
        Token.objects.select_related("user", "user__source_system").filter(user__source_system__isnull=False).all()
    ):
        expiry_date = token.created + expiration_duration
        running_out_soon = (expiry_date - remind_before) < timezone.now()
        if running_out_soon:
            expiring_tokens.append((token, expiry_date))

    return expiring_tokens


def get_tokens_without_expiry_incident(tokens):
    """
    Returns the tokens of the given list that don't have an associated
    expiry incident
    """
    tokens_without_expiry_incident = []
    open_expiry_incidents = Incident.objects.open().token_expiry()

    if not open_expiry_incidents:
        return tokens

    for token, expiry_date in tokens:
        source_system_tag = Tag.objects.filter(
            (Q(key="source_system_id") & Q(value=token.user.source_system.id))
        ).first()

        if not source_system_tag:
            # Expiry incident can't exist since relevant tag doesn't exist
            tokens_without_expiry_incident.append((token, expiry_date))
        else:
            expiry_incident = open_expiry_incidents.filter(incident_tag_relations__tag=source_system_tag).first()
            if expiry_incident:
                open_expiry_incidents.exclude(id=expiry_incident.id)
            else:
                tokens_without_expiry_incident.append((token, expiry_date))

    return tokens_without_expiry_incident


def close_expiry_incidents_without_expiring_tokens(tokens):
    argus_user, _, _ = get_or_create_default_instances()
    open_expiry_incidents = Incident.objects.open().token_expiry()

    if not open_expiry_incidents:
        return

    source_system_tags = []
    for token, expiry_date in tokens:
        source_system_tags.append(
            Tag.objects.filter((Q(key="source_system_id") & Q(value=token.user.source_system.id))).first()
        )

    open_expiry_incidents = open_expiry_incidents.exclude(incident_tag_relations__tag__in=source_system_tags)

    for incident in open_expiry_incidents:
        incident.set_end(actor=argus_user)


class Command(BaseCommand):
    help = "Post incident if token is close to expiring"

    def add_arguments(self, parser):
        parser.add_argument(
            "-d", "--days", default=7, type=int, help="Post incident if token expires in less than <number> days"
        )

    def handle(self, *args, **options):
        expiring_tokens = find_expiring_tokens(options.get("days"))
        tokens_without_expiry_incident = get_tokens_without_expiry_incident(expiring_tokens)

        for token, expiry_date in tokens_without_expiry_incident:
            create_token_expiry_incident(token, expiry_date)

        close_expiry_incidents_without_expiring_tokens(expiring_tokens)
