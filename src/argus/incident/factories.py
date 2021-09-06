import factory, factory.fuzzy
import pytz

from argus.auth.factories import SourceUserFactory
from argus.util.datetime_utils import INFINITY_REPR
from . import models


__all__ = [
    "SourceSystemTypeFactory",
    "SourceSystemFactory",
    "TagFactory",
    "IncidentFactory",
    "StatefulIncidentFactory",
    "StatelessIncidentFactory",
]


class SourceSystemTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SourceSystemType
        django_get_or_create = ("name",)

    name = factory.Faker("word")


class SourceSystemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SourceSystem
        django_get_or_create = ("name", "user")

    name = factory.Faker("word")
    type = factory.SubFactory(SourceSystemTypeFactory)
    user = factory.SubFactory(SourceUserFactory)
    base_url = factory.Faker("url")


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Tag
        django_get_or_create = ("key", "value")

    key = factory.Faker("word")
    value = factory.Faker("word")


class IncidentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Incident

    start_time = factory.Faker("date_time_between", start_date="-1d", end_date="+1d", tzinfo=pytz.UTC)
    end_time = INFINITY_REPR
    source = factory.SubFactory(SourceSystemFactory)
    source_incident_id = factory.Faker("md5")
    details_url = factory.Faker("uri")
    description = factory.Faker("sentence")
    level = factory.fuzzy.FuzzyChoice(models.Incident.LEVELS)  # Random valid level
    ticket_url = factory.Faker("uri")


StatefulIncidentFactory = IncidentFactory


class StatelessIncidentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Incident

    start_time = factory.Faker("date_time_between", start_date="-1d", end_date="+1d", tzinfo=pytz.UTC)
    end_time = None
    source = factory.SubFactory(SourceSystemFactory)
    source_incident_id = factory.Faker("md5")
    details_url = factory.Faker("uri")
    description = factory.Faker("sentence")
    level = factory.fuzzy.FuzzyChoice(models.Incident.LEVELS)  # Random valid level
    ticket_url = factory.Faker("uri")
