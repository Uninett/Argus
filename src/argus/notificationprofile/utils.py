from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Case, F, Value, When
from django.db.models.functions import Concat

from .models import FilterQuerySet

User = get_user_model()


def are_notifications_enabled():
    return getattr(settings, "SEND_NOTIFICATIONS", False)


def annotate_public_filters_with_usernames(qs: FilterQuerySet, user: User = None) -> FilterQuerySet:
    """
    Returns a filter queryset that is annotated with a label that is either the name if
    the filter belongs to the given user or username: name if it belongs to another
    user
    """
    return qs.annotate(
        label=Case(
            When(
                user_id=user.pk,
                then=F("name"),
            ),
            default=Concat("name", Value(" ("), "user__username", Value(")")),
        )
    )
