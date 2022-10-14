from django.test import tag

from rest_framework.test import APITestCase
from argus.auth.factories import PersonUserFactory
from argus.util.testing import disconnect_signals, connect_signals


@tag("integration")
class SignalTests(APITestCase):
    def setUp(self):
        disconnect_signals()

        self.user1 = PersonUserFactory()
        self.user2 = PersonUserFactory(email="")

    def teardown(self):
        connect_signals()

    def test_default_email_destination_should_be_created_if_user_has_email(self):
        # PersonUserFactory creates user with email address
        default_destination = self.user1.destinations.first()
        self.assertTrue(default_destination)
        self.assertTrue(default_destination.settings["synced"])

    def test_default_email_destination_should_not_be_created_if_user_has_no_email(self):
        self.assertFalse(self.user2.destinations.filter(media_id="email", settings__synced=True).exists())

    def test_default_email_destination_should_be_added_if_email_is_added_to_user(self):
        self.user2.email = self.user2.username
        self.user2.save(update_fields=["email"])
        default_destination = self.user2.destinations.first()
        self.assertTrue(default_destination)
        self.assertTrue(default_destination.settings["synced"])

    def test_default_email_destination_should_be_updated_if_user_email_changes(self):
        self.user2.email = "new.email@example.com"
        self.user2.save(update_fields=["email"])
        default_destination = self.user2.destinations.filter(settings__synced=True).first()
        self.assertEqual(self.user2.email, default_destination.settings["email_address"])

    def test_default_email_destination_should_be_deleted_if_user_email_is_deleted(self):
        self.user1.email = ""
        self.user1.save(update_fields=["email"])
        self.assertFalse(self.user1.destinations.filter(settings__synced=True))
