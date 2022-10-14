from datetime import time

import factory

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile import models


__all__ = [
    "TimeslotFactory",
    "TimeRecurrenceFactory",
    "MinimalTimeRecurrenceFactory",
    "MaximalTimeRecurrenceFactory",
    "DestinationConfigFactory",
    "NotificationProfileFactory",
    "FilterFactory",
]


class TimeslotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Timeslot

    user = factory.SubFactory(PersonUserFactory)
    name = factory.Sequence(lambda s: "Timeslot %s" % s)


class TimeRecurrenceFactory(factory.django.DjangoModelFactory):
    "A random TimeRecurrence"

    class Meta:
        model = models.TimeRecurrence

    timeslot = factory.SubFactory(TimeslotFactory)
    start = factory.Faker("time_object")
    end = factory.Faker("time_object")
    days = factory.Faker("random_sample", elements=[models.TimeRecurrence.Day])


class MinimalTimeRecurrenceFactory(TimeRecurrenceFactory):
    "A TimeRecurrence that should just about never occur"
    start = time(hour=5, minute=0)
    end = start
    days = [7]


class MaximalTimeRecurrenceFactory(TimeRecurrenceFactory):
    "A TimeRecurrence that always occurs"

    class Meta:
        model = models.TimeRecurrence

    timeslot = factory.SubFactory(TimeslotFactory)
    start = time.min
    end = time.max
    days = list(range(1, 7 + 1))


class MediaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Media

    slug = factory.Sequence(lambda s: "Media %s" % s)
    name = factory.LazyAttribute(lambda obj: obj.slug.capitalize())


class DestinationConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.DestinationConfig

    user = factory.SubFactory(PersonUserFactory)
    media = factory.SubFactory(MediaFactory)


class NotificationProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.NotificationProfile

    user = factory.SubFactory(PersonUserFactory, user=factory.SelfAttribute("..timeslot"))
    timeslot = factory.SubFactory(TimeslotFactory)
    active = factory.Faker("boolean")


class FilterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Filter

    user = factory.SubFactory(PersonUserFactory)
    name = factory.Sequence(lambda s: "Filter %s" % s)
    filter_string = '{"sourceSystemIds": [], "tags": []}'
