import factory

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile.factories import TimeslotFactory
from argus.notificationprofile.models import NotificationProfile


__all__ = [
    "NotificationProfileFactoryV1",
]


class NotificationProfileFactoryV1(factory.django.DjangoModelFactory):
    class Meta:
        model = NotificationProfile

    user = factory.SubFactory(PersonUserFactory, user=factory.SelfAttribute("..timeslot"))
    timeslot = factory.SubFactory(TimeslotFactory)
    media_v1 = NotificationProfile.Media.EMAIL
    active = factory.Faker("boolean")
