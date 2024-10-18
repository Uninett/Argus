from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from argus.auth.factories import PersonUserFactory, SourceUserFactory
from argus.incident.factories import SourceSystemFactory


User = get_user_model()


class UserTests(TestCase):
    def test_is_end_user(self):
        user = PersonUserFactory()
        self.assertTrue(user.is_end_user)

    def test_is_source_system(self):
        user = SourceUserFactory()
        ss = SourceSystemFactory(user=user)
        self.assertTrue(user.is_source_system)

    def test_is_member_of_group_when_no_groups_returns_none(self):
        user = PersonUserFactory()
        self.assertEqual(user.is_member_of_group("blbl"), None)

    def test_is_member_of_group_when_group_is_str_succeeds(self):
        user = PersonUserFactory()
        group = Group.objects.create(name="fjoon")
        user.groups.add(group)
        self.assertTrue(user.is_member_of_group(group.name))

    def test_is_member_of_group_when_group_is_group_succeeds(self):
        user = PersonUserFactory()
        group = Group.objects.create(name="brrrr")
        user.groups.add(group)
        self.assertTrue(user.is_member_of_group(group))

    def test_is_member_of_group_when_not_member_of_group_fails(self):
        user = PersonUserFactory()
        group = Group.objects.create(name="foobar")
        self.assertFalse(user.is_member_of_group(group))
