from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

from argus.auth.factories import PersonUserFactory
from tests.auth.models import MyPreferences
from argus.auth.utils import save_preferences

User = get_user_model()


class SavePreferencesTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/not-relevant")
        self.user = self.request.user = PersonUserFactory()
        SessionMiddleware(lambda x: x).process_request(self.request)
        MessageMiddleware(lambda x: x).process_request(self.request)

        self.assertTrue(self.request.user.is_authenticated)

    def assertSuccesfulUpdate(self, success, fail):
        self.assertEqual(success, ["magic_number"])
        self.assertEqual(fail, [])

    def assertFailedUpdate(self, success, fail):
        self.assertEqual(success, [])
        self.assertEqual(fail, ["magic_number"])

    def test_save_preferences_succesfully(self):
        success, fail = save_preferences(self.request, {"magic_number": 43}, "mypref")
        self.assertSuccesfulUpdate(success, fail)

    def test_save_preferences_by_model(self):
        success, fail = save_preferences(self.request, {"magic_number": 43}, MyPreferences(user=self.user))
        self.assertSuccesfulUpdate(success, fail)

    def test_not_changing_preference_counts_as_success(self):
        success, fail = save_preferences(self.request, {"magic_number": 42}, "mypref")
        self.assertSuccesfulUpdate(success, fail)

    def test_invalid_form_fails(self):
        success, fail = save_preferences(self.request, {"magic_number": "not-a-number"}, "mypref")
        self.assertFailedUpdate(success, fail)
