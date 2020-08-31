import factory

from .models import *


class PersonUserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = User
        django_get_or_create = ('username',)

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda o: '%s.%s@%s' % (o.first_name.lower(), o.last_name.lower(), factory.Faker('safe_domain_name')))
    username = email
    is_staff = False
    is_superuser = False
    password = factory.Faker('password')


class SourceUserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = factory.Faker('word')
    is_staff = False
    is_superuser = False


class AdminUserFactory(PersonUserFactory):
    is_staff = True
    is_superuser = True
