import factory
import pytz

from argus.auth.factories import SourceUserFactory
from . import models


__all__ = [
    "SourceSystemTypeFactory",
    "SourceSystemFactory",
    "TagFactory",
    "IncidentFactory",
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
    end_time = "infinity"
    source = factory.SubFactory(SourceSystemFactory)
    source_incident_id = factory.Faker("md5")
    details_url = factory.Faker("uri")
    description = factory.Faker("sentence")
    ticket_url = factory.Faker("uri")
