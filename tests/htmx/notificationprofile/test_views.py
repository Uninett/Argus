from django.test import TestCase, override_settings
from django.urls import reverse

from argus.auth.factories import PersonUserFactory


@override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
class NotificationProfileViewTestCase(TestCase):
    def setUp(self):
        self.user = PersonUserFactory()
        self.client.force_login(user=self.user)


class TestNotificationProfileListView(NotificationProfileViewTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("htmx:notificationprofile-list")

    def test_context_has_active_tab_profiles(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "profiles")

    def test_context_has_page_title(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_title"], "Profiles")
