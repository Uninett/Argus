"""
This shows how to write a test-case for testing a data-migration!
"""

from unittest import skip

from django.test import TestCase

from tests.helpers import Migrator


@skip
class ExampleMigrationTest(TestCase):
    base_migration = ("someapp", "0003_nonexistent")
    test_migration = ("someapp", "0004_datamigration")

    def setUp(self):
        self.migrator = Migrator()
        self.migrator.migrate(*self.base_migration)

    # testing the forwards migration

    def test_forward_when_nothing_to_change_then_changes_nothing(self):
        # datamigration where we don't find anything to change
        MyModel = self.migrator.apps.get_model("someapp", "MyModel")

        # add some data to MyModel
        ...

        # run the migration in test_migration
        self.migrator.migrate(*self.test_migration)  # Note

        # check that nothing changed
        result = MyModel.objects.filter(something="blah")
        self.assertFalse(result)

    def test_forward_when_something_to_change_then_changes_something(self):
        # datamigration where we do change existing data
        MyModel = self.migrator.apps.get_model("someapp", "MyModel")

        # add some data to MyModel
        ...

        # run the migration in test_migration
        self.migrator.migrate(*self.test_migration)  # Note

        # check that something changed
        result = MyModel.objects.filter(something="blah")
        self.assertTrue(result)

    # testing the backwards migration

    def test_backward_when_nothing_to_change_then_changes_nothing(self):
        # datamigration where we don't find anything to change
        MyModel = self.migrator.apps.get_model("someapp", "MyModel")

        # add some data to MyModel
        ...

        # run the migration in test_migration
        self.migrator.migrate(*self.test_migration)  # Note 1

        # then ALSO run the migration in base_migration!
        self.migrator.migrate(*self.base_migration)  # Note 2

        # check that nothing changed
        result = MyModel.objects.filter(something="blah")
        self.assertFalse(result)

    def test_backward_when_something_to_change_then_changes_something(self):
        # datamigration where we don't find anything to change
        MyModel = self.migrator.apps.get_model("someapp", "MyModel")

        # add some data to MyModel
        ...

        # run the migration in test_migration
        self.migrator.migrate(*self.test_migration)  # Note 1

        # then ALSO run the migration in base_migration!
        self.migrator.migrate(*self.base_migration)  # Note 2

        # check that something changed
        result = MyModel.objects.filter(something="blah")
        self.assertTrue(result)
