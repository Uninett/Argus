from django.test import Client
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from argus.auth.models import User
from .models import AlertSource, AlertSourceType


class AlertSourcePostingTests(APITestCase):
    def setUp(self):
        self.type1 = AlertSourceType.objects.create(name="NAV")
        self.type2 = AlertSourceType.objects.create(name="Zabbix")

        password = "1234"
        self.user1 = User.objects.create_user(
            username="user1", password=password, is_staff=True, is_superuser=True,
        )
        user_token = Token.objects.create(user=self.user1)

        self.rest_client = APIClient()
        self.rest_client.credentials(HTTP_AUTHORIZATION="Token " + user_token.key)
        self.django_client = Client()
        self.django_client.login(username=self.user1.username, password=password)

        # URL format: https://docs.djangoproject.com/en/3.0/ref/contrib/admin/#reversing-admin-urls
        self.base_admin_url = (
            f"admin:{AlertSource._meta.app_label}_{AlertSource._meta.model_name}"
        )
        self.add_url = reverse(f"{self.base_admin_url}_add")
        self.change_url = lambda alert_source: reverse(
            f"{self.base_admin_url}_change", args=[alert_source.pk]
        )
        self.sources_url = reverse("alert:sources")

    def _post_source1_dict(self, url: str, client: Client):
        self.source1_dict = {
            "name": "NAV 1",
            "type": self.type1.pk,
            "username": "gw1.uninett.no",
        }
        client.post(url, self.source1_dict)

    def _test_posting_should_add_alert_source_with_user(self, url: str, client: Client):
        self.assertEqual(AlertSource.objects.count(), 0)
        self._post_source1_dict(url, client)
        self.assertEqual(AlertSource.objects.count(), 1)

        source1 = AlertSource.objects.get(name=self.source1_dict["name"])
        self.assertEqual(source1.name, self.source1_dict["name"])
        self.assertEqual(source1.type.pk, self.source1_dict["type"])
        self.assertEqual(source1.user.username, self.source1_dict["username"])

    def test_serializer_should_add_alert_source_with_user(self):
        self._test_posting_should_add_alert_source_with_user(self.sources_url, self.rest_client)

    def test_admin_add_form_should_add_alert_source_with_user(self):
        self._test_posting_should_add_alert_source_with_user(self.add_url, self.django_client)

    def _test_posting_duplicate_alert_source_name_should_not_add_objects(self, url: str, client: Client):
        self._post_source1_dict(url, client)

        source1_duplicate_name = {
            "name": self.source1_dict["name"],
            "type": self.source1_dict["type"],
            "username": "gw2.uninett.no",
        }
        client.post(url, source1_duplicate_name)
        self.assertEqual(AlertSource.objects.count(), 1)

    def test_serializer_posting_duplicate_alert_source_name_should_not_add_objects(self):
        self._test_posting_duplicate_alert_source_name_should_not_add_objects(self.sources_url, self.rest_client)

    def test_admin_add_form_posting_duplicate_alert_source_name_should_not_add_objects(self):
        self._test_posting_duplicate_alert_source_name_should_not_add_objects(self.add_url, self.django_client)

    def _test_posting_duplicate_alert_source_username_should_not_add_objects(self, url: str, client: Client):
        source1_duplicate_username = {
            "name": "NAV 2",
            "type": self.type2.pk,
            "username": self.source1_dict["username"],
        }
        client.post(url, source1_duplicate_username)
        self.assertEqual(AlertSource.objects.count(), 1)

    def test_serializer_posting_duplicate_alert_source_username_should_not_add_objects(self):
        self._post_source1_dict(self.sources_url, self.rest_client)
        self._test_posting_duplicate_alert_source_username_should_not_add_objects(self.sources_url, self.rest_client)

    def test_admin_add_form_posting_duplicate_alert_source_username_should_not_add_objects(self):
        self._post_source1_dict(self.add_url, self.django_client)
        self._test_posting_duplicate_alert_source_username_should_not_add_objects(self.add_url, self.django_client)

    def test_admin_change_form_should_change_fields(self):
        source1_user = User.objects.create_user(username="gw1.uninett.no")
        source1_user2 = User.objects.create_user(username="new.gw1.uninett.no")
        source1 = AlertSource.objects.create(
            name="NAV 1", type=self.type1, user=source1_user,
        )

        source1_dict = {
            "name": "New NAV 1",
            "type": self.type2,
            "user": source1_user2.pk,
        }
        self.django_client.post(self.change_url(source1), source1_dict)
        source1.refresh_from_db()
        self.assertEqual(source1.name, source1_dict["name"])
        self.assertEqual(source1.type, source1_dict["type"])
        self.assertEqual(source1.user.pk, source1_dict["user"])
