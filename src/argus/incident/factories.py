from zoneinfo import ZoneInfo
from datetime import datetime
from random import randint, choice
from typing import Optional, Any

from django.core.exceptions import ValidationError
from django.utils import timezone

import factory
import factory.fuzzy

from argus.auth.factories import SourceUserFactory
from argus.util.datetime_utils import INFINITY, INFINITY_REPR
from .models import (
    Tag,
    Incident,
    IncidentTagRelation,
    SourceSystemType,
    SourceSystem,
    Event,
    Acknowledgement,
    get_or_create_default_instances,
)
from .constants import Level
from .serializers import IncidentSerializer


__all__ = [
    "SourceSystemTypeFactory",
    "SourceSystemFactory",
    "TagFactory",
    "IncidentFactory",
    "IncidentTagRelationFactory",
    "StatefulIncidentFactory",
    "StatelessIncidentFactory",
]


def update_tags(incident: Incident, *tags):
    """Update an existing incident's tags"""
    argus_user, _, _ = get_or_create_default_instances()
    c = 0
    for tag in tags:
        tag = Tag.objects.create_from_tag(tag)
        _, created = IncidentTagRelation.objects.get_or_create(tag=tag, incident=incident, added_by=argus_user)
        c += 1 if created else 0
    return c


def create_fake_incident(
    tags: Optional[list[str]] = None,
    description: Optional[str] = None,
    source: Optional[str] = None,
    stateful: bool = True,
    level: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = INFINITY_REPR,
    source_incident_id: Optional[str] = None,
    details_url: Optional[str] = None,
    ticket_url: Optional[str] = None,
    **kwargs,
):
    if not source:
        _, _, source = get_or_create_default_instances()
    else:
        try:
            source = SourceSystem.objects.get(name=source)
        except SourceSystem.DoesNotExist:
            raise ValueError(f"No source with the name '{source}' exists.")

    MAX_ID = 2**32 - 1
    MIN_ID = 1
    if source_incident_id is None:
        source_incident_id = randint(MIN_ID, MAX_ID)

    if not description:
        if stateful:
            description = f'Incident #{source_incident_id} created via "create_fake_incident"'
        else:
            description = f'Incident (stateless) #{source_incident_id} created via "create_fake_incident"'

    if not tags:
        tags = ["location=argus", f"object={source_incident_id}", "problem_type=test"]

    level = level or choice(Level.values)

    return create_incident(
        description,
        source,
        stateful,
        level,
        tags=tags,
        metadata=metadata,
        start_time=start_time,
        end_time=end_time,
        source_incident_id=source_incident_id,
        details_url=details_url,
        ticket_url=ticket_url,
    )


def create_incident(
    description: str,
    source: SourceSystem,
    stateful: bool,
    level: int,
    tags: Optional[list[str]] = None,
    metadata: dict[str, Any] = None,
    start_time: Optional[str | datetime] = None,
    end_time: Optional[str | datetime] = None,
    source_incident_id: Optional[str] = None,
    details_url: Optional[str] = None,
    ticket_url: Optional[str] = None,
):
    data = {
        "description": description,
        "level": level,
        "metadata": metadata if metadata else {},
        "source": source,
        "stateful": stateful,
    }

    # IncidentSerializer expects following form for tags
    # [{"tag":"a=b"}, ...]
    tags_serializer_format = []
    if tags is not None:
        for tag in tags:
            tags_serializer_format.append({"tag": tag})
    data["tags"] = tags_serializer_format

    if start_time is None:
        start_time = str(timezone.now())
    elif isinstance(start_time, datetime):
        start_time = start_time.isoformat()
    data["start_time"] = start_time

    # IncidentSerializer expects following input for end_time
    # stateless: end_time=None
    # stateful & open: end_time missing
    # stateful & closed: end_time=timestamp
    if stateful:
        if end_time in (INFINITY, INFINITY_REPR):
            data.pop("end_time", None)
        elif isinstance(end_time, datetime):
            end_time = end_time.isoformat()
    else:
        end_time = None
    data["end_time"] = end_time

    if details_url:
        data["details_url"] = details_url
    if ticket_url:
        data["ticket_url"] = ticket_url
    if source_incident_id:
        data["source_incident_id"] = str(source_incident_id)

    serializer = IncidentSerializer(data=data)
    if serializer.is_valid():
        incident_exists = Incident.objects.filter(source=source, source_incident_id=source_incident_id).exists()
        if incident_exists and source_incident_id:
            raise ValidationError("Source incident ids need to be unique for each source.")
        incident = serializer.save(user=source.user, source=source)
    else:
        raise ValidationError(serializer.errors)

    return incident


def create_stateful_incident(
    description: str,
    source: SourceSystem,
    level: int,
    tags: Optional[list[str]] = None,
    metadata: dict[str, Any] = None,
    start_time: Optional[datetime] = None,
    source_incident_id: Optional[str] = None,
    details_url: Optional[str] = None,
    ticket_url: Optional[str] = None,
):
    stateful = True
    end_time = INFINITY
    return create_incident(
        description,
        source,
        stateful,
        level,
        tags=tags,
        metadata=metadata,
        start_time=start_time,
        end_time=end_time,
        source_incident_id=source_incident_id,
        details_url=details_url,
        ticket_url=ticket_url,
    )


def create_stateless_incident(
    description: str,
    source: SourceSystem,
    level: int,
    tags: Optional[list[str]] = None,
    metadata: dict[str, Any] = None,
    start_time: Optional[datetime] = None,
    source_incident_id: Optional[str] = None,
    details_url: Optional[str] = None,
    ticket_url: Optional[str] = None,
):
    stateful = False
    end_time = None
    return create_incident(
        description,
        source,
        stateful,
        level,
        tags=tags,
        metadata=metadata,
        start_time=start_time,
        end_time=end_time,
        source_incident_id=source_incident_id,
        details_url=details_url,
        ticket_url=ticket_url,
    )


def create_token_expiry_incident(token, expiry_date, level=2):
    if not token:
        raise ValueError("Token must be not None")

    _, _, source_system = get_or_create_default_instances()
    description = f"Token for source system {str(token.user.source_system)} will expire on {expiry_date.date()}"

    tags = [
        "location=argus",
        "problem_type=token_expiry",
        f"source_system_id={token.user.source_system.id}",
    ]
    incident = create_stateful_incident(
        description,
        source_system,
        level,
        tags=tags,
        start_time=timezone.now(),
    )
    update_tags(incident, f"object={incident.id}")
    incident.source_incident_id = incident.id
    incident.save()
    return incident


class SourceSystemTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SourceSystemType
        # When calling this factory with a potentially not lowercase name make
        # sure to force the name into lowercase first, since get_or_create
        # cares about cases, but SourceSystemType.save() makes it lowercase
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda s: "SourceSystemType %s" % s)


class SourceSystemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SourceSystem
        django_get_or_create = ("name", "user")

    name = factory.Sequence(lambda s: "SourceSystem %s" % s)
    type = factory.SubFactory(SourceSystemTypeFactory)
    user = factory.SubFactory(SourceUserFactory)
    base_url = factory.Faker("url")
    last_seen = None
    heartbeat_frequency = None


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag
        django_get_or_create = ("key", "value")

    key = factory.Sequence(lambda s: "key_%s" % s)
    value = factory.Sequence(lambda s: "value_%s" % s)


class IncidentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Incident

    start_time = factory.Faker("date_time_between", start_date="-1d", end_date="+1d", tzinfo=ZoneInfo("UTC"))
    end_time = INFINITY_REPR
    source = factory.SubFactory(SourceSystemFactory)
    source_incident_id = factory.Sequence(lambda s: str(s))
    details_url = factory.Faker("uri")
    description = factory.Faker("sentence")
    level = factory.fuzzy.FuzzyChoice(Level.values)  # Random valid level
    ticket_url = factory.Faker("uri")


class StatefulIncidentFactory(IncidentFactory):
    pass


class StatelessIncidentFactory(IncidentFactory):
    end_time = None


class IncidentTagRelationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IncidentTagRelation

    tag = factory.SubFactory(TagFactory)
    incident = factory.SubFactory(IncidentFactory)
    added_by = factory.SubFactory(SourceUserFactory)
    added_time = factory.Faker("date_time_between", start_date="-1d", end_date="+1d", tzinfo=ZoneInfo("UTC"))


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    incident = factory.SubFactory(IncidentFactory)
    actor = factory.SubFactory(SourceUserFactory)
    timestamp = factory.Faker("date_time_between", start_date="-1d", end_date="+1d", tzinfo=ZoneInfo("UTC"))
    received = timestamp
    type = Event.Type.OTHER
    description = factory.Faker("sentence")


class AcknowledgementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Acknowledgement

    event = factory.SubFactory(EventFactory, type=Event.Type.ACKNOWLEDGE)
    expiration = factory.Faker("date_time_between", start_date="+1d", end_date="+2d", tzinfo=ZoneInfo("UTC"))
