import factory

from argus.auth.factories import PersonUserFactory
from argus.htmx.user.preferences.models import ArgusHtmxPreferences


class ArgusHtmxPreferencesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ArgusHtmxPreferences

    user = factory.SubFactory(PersonUserFactory)
    namespace = "argus_htmx"
    preferences = dict()
