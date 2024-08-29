from django.test import TestCase

from tests.helpers import Migrator


class MigrationTest(TestCase):
    base_migration = ("argus_notificationprofile", "0016_noop")
    test_migration = ("argus_notificationprofile", "0017_change_event_type_to_event_types")

    def setUp(self):
        self.migrator = Migrator()
        self.migrator.migrate(*self.base_migration)

    def test_forward_empty_changes_nothing(self):
        # Cannot use factories :(
        User = self.migrator.apps.get_model("argus_auth", "User")
        Filter = self.migrator.apps.get_model("argus_notificationprofile", "Filter")
        user = User.objects.create(username="foo", password="vbnh")

        filter_ = Filter.objects.create(
            user=user,
            name="1",
            filter={},
        )
        self.migrator.migrate(*self.test_migration)
        result = Filter.objects.get(id=filter_.pk)
        self.assertEqual(result.filter, {})

    def test_forward_remove_redundant_filter(self):
        # Cannot use factories :(
        User = self.migrator.apps.get_model("argus_auth", "User")
        Filter = self.migrator.apps.get_model("argus_notificationprofile", "Filter")
        user = User.objects.create(username="foo", password="vbnh")

        filter_ = Filter.objects.create(
            user=user,
            name="1",
            filter={"event_type": None},
        )
        self.migrator.migrate(*self.test_migration)
        result = Filter.objects.get(id=filter_.pk)
        self.assertEqual(result.filter, {})

    def test_forward_change_actual_filter(self):
        # Cannot use factories :(
        User = self.migrator.apps.get_model("argus_auth", "User")
        Filter = self.migrator.apps.get_model("argus_notificationprofile", "Filter")
        user = User.objects.create(username="foo", password="vbnh")

        filter_ = Filter.objects.create(
            user=user,
            name="1",
            filter={"event_type": "BAH HUMBUG"},
        )
        self.migrator.migrate(*self.test_migration)
        result = Filter.objects.get(id=filter_.pk)
        self.assertEqual(result.filter, {"event_types": ["BAH HUMBUG"]})

    def test_backward_empty_changes_nothing(self):
        # Cannot use factories :(
        User = self.migrator.apps.get_model("argus_auth", "User")
        Filter = self.migrator.apps.get_model("argus_notificationprofile", "Filter")
        user = User.objects.create(username="foo", password="vbnh")

        filter_ = Filter.objects.create(
            user=user,
            name="1",
            filter={},
        )
        self.migrator.migrate(*self.test_migration)
        self.migrator.migrate(*self.base_migration)
        result = Filter.objects.get(id=filter_.pk)
        self.assertEqual(result.filter, {})

    def test_backward_remove_redundant_filter(self):
        # Cannot use factories :(
        User = self.migrator.apps.get_model("argus_auth", "User")
        Filter = self.migrator.apps.get_model("argus_notificationprofile", "Filter")
        user = User.objects.create(username="foo", password="vbnh")

        filter_ = Filter.objects.create(
            user=user,
            name="1",
            filter={},
        )
        self.migrator.migrate(*self.test_migration)
        filter_.filter = {"event_types": []}
        self.migrator.migrate(*self.base_migration)
        result = Filter.objects.get(id=filter_.pk)
        self.assertEqual(result.filter, {})

    def test_backward_dont_recreate_redundant_filter(self):
        # Cannot use factories :(
        User = self.migrator.apps.get_model("argus_auth", "User")
        Filter = self.migrator.apps.get_model("argus_notificationprofile", "Filter")
        user = User.objects.create(username="foo", password="vbnh")

        filter_ = Filter.objects.create(
            user=user,
            name="1",
            filter={"event_type": None},
        )
        self.migrator.migrate(*self.test_migration)
        self.migrator.migrate(*self.base_migration)
        result = Filter.objects.get(id=filter_.pk)
        self.assertEqual(result.filter, {})

    def test_backward_change_actual_filter(self):
        # Cannot use factories :(
        User = self.migrator.apps.get_model("argus_auth", "User")
        Filter = self.migrator.apps.get_model("argus_notificationprofile", "Filter")
        user = User.objects.create(username="foo", password="vbnh")

        filter_ = Filter.objects.create(
            user=user,
            name="1",
            filter={"event_type": "BAH HUMBUG"},
        )
        self.migrator.migrate(*self.test_migration)
        self.migrator.migrate(*self.base_migration)
        result = Filter.objects.get(id=filter_.pk)
        self.assertEqual(result.filter, {"event_type": "BAH HUMBUG"})
