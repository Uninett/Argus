import factory

from .models import User

__all__ = [
    "PersonUserFactory",
    "SourceUserFactory",
    "AdminUserFactory",
]


class BaseUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    is_staff = False
    is_superuser = False
    password = factory.PostGenerationMethodCall("set_password", "defaultpassword")


class PersonUserFactory(BaseUserFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(
        lambda o: "%s.%s@%s" % (o.first_name.lower(), o.last_name.lower(), factory.Faker("safe_domain_name"))
    )
    username = email


class SourceUserFactory(BaseUserFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Faker("word")
    is_staff = False
    is_superuser = False


class AdminUserFactory(PersonUserFactory):
    is_staff = True
    is_superuser = True
