from zoneinfo import ZoneInfo

import factory
import factory.fuzzy

from argus.auth.factories import SourceUserFactory
from argus.util.datetime_utils import INFINITY_REPR
from . import models
from .constants import Level


__all__ = [
    "SourceSystemTypeFactory",
    "SourceSystemFactory",
    "TagFactory",
    "IncidentFactory",
    "IncidentTagRelationFactory",
    "StatefulIncidentFactory",
    "StatelessIncidentFactory",
]


class SourceSystemTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SourceSystemType
        # When calling this factory with a potentially not lowercase name make
        # sure to force the name into lowercase first, since get_or_create
        # cares about cases, but SourceSystemType.save() makes it lowercase
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda s: "SourceSystemType %s" % s)


class SourceSystemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SourceSystem
        django_get_or_create = ("name", "user")

    name = factory.Sequence(lambda s: "SourceSystem %s" % s)
    type = factory.SubFactory(SourceSystemTypeFactory)
    user = factory.SubFactory(SourceUserFactory)
    base_url = factory.Faker("url")


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Tag
        django_get_or_create = ("key", "value")

    key = factory.Sequence(lambda s: "key_%s" % s)
    value = factory.Sequence(lambda s: "value_%s" % s)


class IncidentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Incident

    start_time = factory.Faker("date_time_between", start_date="-1d", end_date="+1d", tzinfo=ZoneInfo("UTC"))
    end_time = INFINITY_REPR
    source = factory.SubFactory(SourceSystemFactory)
    source_incident_id = factory.Sequence(lambda s: s)
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
        model = models.IncidentTagRelation

    tag = factory.SubFactory(TagFactory)
    incident = factory.SubFactory(IncidentFactory)
    added_by = factory.SubFactory(SourceUserFactory)
    added_time = factory.Faker("date_time_between", start_date="-1d", end_date="+1d", tzinfo=ZoneInfo("UTC"))


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Event

    incident = factory.SubFactory(IncidentFactory)
    actor = factory.SubFactory(SourceUserFactory)
    timestamp = factory.Faker("date_time_between", start_date="-1d", end_date="+1d", tzinfo=ZoneInfo("UTC"))
    received = timestamp
    type = models.Event.Type.OTHER
    description = factory.Faker("sentence")


class AcknowledgementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Acknowledgement

    event = factory.SubFactory(EventFactory, type=models.Event.Type.ACKNOWLEDGE)
    expiration = factory.Faker("date_time_between", start_date="+1d", end_date="+2d", tzinfo=ZoneInfo("UTC"))
