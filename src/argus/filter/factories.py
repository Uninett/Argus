import factory

from argus.auth.factories import PersonUserFactory
from argus.notificationprofile import models


__all__ = [
    "FilterFactory",
]


class FilterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Filter

    user = factory.SubFactory(PersonUserFactory)
    name = factory.Sequence(lambda s: "Filter %s" % s)
    filter = dict()
