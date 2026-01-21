from django.test import TestCase

from argus.auth.factories import AdminUserFactory
from argus.filter.factories import FilterFactory
from argus.notificationprofile.models import Filter


class TestFilterQuerySet(TestCase):
    def setUp(self):
        self.user1 = AdminUserFactory()
        self.user2 = AdminUserFactory()

    def test_editable_by(self):
        filter1 = FilterFactory(user=self.user1)
        filter2 = FilterFactory(user=self.user2)
        result = Filter.objects.editable_by(self.user1)
        self.assertEqual(len(result), 1)
        self.assertIn(filter1, result)
        self.assertNotIn(filter2, result)

    def test_usable_by(self):
        filter1 = FilterFactory(user=self.user1)
        filter2 = FilterFactory(user=self.user2)
        filter3 = FilterFactory(user=self.user2, public=True)
        result = Filter.objects.usable_by(self.user1)
        self.assertEqual(len(result), 2)
        self.assertIn(filter1, result)
        self.assertIn(filter3, result)
        self.assertNotIn(filter2, result)


class TestFilterMethods(TestCase):
    def setUp(self):
        self.user1 = AdminUserFactory()
        self.user2 = AdminUserFactory()

    def test_editable_by(self):
        filter1 = FilterFactory(user=self.user1)
        filter2 = FilterFactory(user=self.user2)
        filter3 = FilterFactory(user=self.user2, public=True)
        self.assertTrue(filter1.editable_by(self.user1))
        self.assertFalse(filter2.editable_by(self.user1))
        self.assertFalse(filter3.editable_by(self.user1))
