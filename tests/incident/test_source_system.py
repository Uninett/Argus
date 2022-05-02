from django.test import Client
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from argus.auth.models import User
from argus.auth.factories import AdminUserFactory
from argus.incident.factories import SourceSystemTypeFactory
from argus.incident.models import SourceSystem


class SourceSystemPostingTests(APITestCase):
    def setUp(self):
        self.type1 = SourceSystemTypeFactory(name="nav")
        self.type2 = SourceSystemTypeFactory(name="zabbix")

        password = "1234"
        self.user1 = AdminUserFactory(username="user1", password=password)
        user_token = Token.objects.create(user=self.user1)

        self.rest_client = APIClient()
        self.rest_client.credentials(HTTP_AUTHORIZATION=f"Token {user_token.key}")
        self.django_client = Client()
        self.django_client.login(username=self.user1.username, password=password)

        # URL format: https://docs.djangoproject.com/en/3.0/ref/contrib/admin/#reversing-admin-urls
        self.base_admin_url = f"admin:{SourceSystem._meta.app_label}_{SourceSystem._meta.model_name}"
        self.add_url = reverse(f"{self.base_admin_url}_add")
        self.change_url = lambda source_system: reverse(f"{self.base_admin_url}_change", args=[source_system.pk])
        self.sources_url = reverse("v1:incident:sourcesystem-list")

    def _post_source1_dict(self, url: str, client: Client):
        self.source1_dict = {
            "name": "gw1.sikt",
            "type": self.type1.pk,
            "username": "gw1.sikt",
        }
        client.post(url, self.source1_dict)

    def _test_posting_should_add_source_system_with_user(self, url: str, client: Client):
        self.assertEqual(SourceSystem.objects.count(), 0)
        self.assertEqual(User.objects.count(), 1)
        self._post_source1_dict(url, client)
        self.assertEqual(SourceSystem.objects.count(), 1)
        self.assertEqual(User.objects.count(), 2)

        source1 = SourceSystem.objects.get(name=self.source1_dict["name"])
        self.assertEqual(source1.name, self.source1_dict["name"])
        self.assertEqual(source1.type.pk, self.source1_dict["type"])
        self.assertEqual(source1.user.username, self.source1_dict["username"])

    def test_serializer_should_add_source_system_with_user(self):
        self._test_posting_should_add_source_system_with_user(self.sources_url, self.rest_client)

    def test_admin_add_form_should_add_source_system_with_user(self):
        self._test_posting_should_add_source_system_with_user(self.add_url, self.django_client)

    def _test_posting_duplicate_source_system_name_should_not_add_objects(self, url: str, client: Client):
        self._post_source1_dict(url, client)

        source1_duplicate_name = {
            "name": self.source1_dict["name"],
            "type": self.source1_dict["type"],
            "username": "gw2.sikt",
        }
        self.assertEqual(SourceSystem.objects.count(), 1)
        self.assertEqual(User.objects.count(), 2)
        client.post(url, source1_duplicate_name)
        self.assertEqual(SourceSystem.objects.count(), 1)
        self.assertEqual(User.objects.count(), 2)

    def test_posting_duplicate_source_system_name_to_serializer_should_not_add_objects(self):
        self._test_posting_duplicate_source_system_name_should_not_add_objects(self.sources_url, self.rest_client)

    def test_posting_duplicate_source_system_name_to_admin_add_form_should_not_add_objects(self):
        self._test_posting_duplicate_source_system_name_should_not_add_objects(self.add_url, self.django_client)

    def _test_posting_duplicate_source_system_username(self, url: str, client: Client):
        self._post_source1_dict(url, client)
        self.source1_duplicate_username_dict = {
            "name": "gw2.sikt",
            "type": self.type2.pk,
            "username": self.source1_dict["username"],
        }
        self.assertEqual(SourceSystem.objects.count(), 1)
        self.assertEqual(User.objects.count(), 2)
        client.post(url, self.source1_duplicate_username_dict)

    def test_posting_duplicate_source_system_username_to_serializer_should_set_username_with_generated_suffix(self):
        self._test_posting_duplicate_source_system_username(self.sources_url, self.rest_client)
        self.assertEqual(SourceSystem.objects.count(), 2)
        self.assertEqual(User.objects.count(), 3)

        source1_duplicate_username = SourceSystem.objects.get(name=self.source1_duplicate_username_dict["name"])
        self.assertEqual(source1_duplicate_username.name, self.source1_duplicate_username_dict["name"])
        self.assertEqual(source1_duplicate_username.type.pk, self.source1_duplicate_username_dict["type"])
        duplicate_username = self.source1_duplicate_username_dict["username"]
        generated_username = source1_duplicate_username.user.username
        self.assertNotEqual(generated_username, duplicate_username)
        self.assertTrue(generated_username.startswith(duplicate_username))

    def test_posting_duplicate_source_system_username_to_admin_add_form_should_not_add_objects(self):
        self._test_posting_duplicate_source_system_username(self.add_url, self.django_client)
        self.assertEqual(SourceSystem.objects.count(), 1)
        self.assertEqual(User.objects.count(), 2)

    def _test_posting_empty_source_system_username_should_use_source_system_name_as_username(
        self, url: str, client: Client
    ):
        source_name = "gw.sikt"
        source_no_username_dict = {
            "name": source_name,
            "type": self.type1.pk,
        }
        self.assertEqual(SourceSystem.objects.count(), 0)
        self.assertEqual(User.objects.count(), 1)
        client.post(url, source_no_username_dict)
        self.assertEqual(SourceSystem.objects.count(), 1)
        self.assertEqual(User.objects.count(), 2)

        source = SourceSystem.objects.get(name=source_name)
        self.assertEqual(source.user.username, source_name)

    def test_posting_empty_source_system_username_to_serializer_should_use_source_system_name_as_username(self):
        self._test_posting_empty_source_system_username_should_use_source_system_name_as_username(
            self.sources_url, self.rest_client
        )

    def test_posting_empty_source_system_username_to_admin_add_form_should_use_source_system_name_as_username(self):
        self._test_posting_empty_source_system_username_should_use_source_system_name_as_username(
            self.add_url, self.django_client
        )

    def test_admin_change_form_should_change_fields(self):
        source1_user = User.objects.create_user(username="gw1.sikt")
        source1_user2 = User.objects.create_user(username="new.gw1.sikt")
        source1 = SourceSystem.objects.create(name="gw1.sikt", type=self.type1, user=source1_user)

        source1_dict = {
            "name": "new.gw1.sikt",
            "type": self.type2,
            "user": source1_user2.pk,
        }
        self.django_client.post(self.change_url(source1), source1_dict)
        source1.refresh_from_db()
        self.assertEqual(source1.name, source1_dict["name"])
        self.assertEqual(source1.type, source1_dict["type"])
        self.assertEqual(source1.user.pk, source1_dict["user"])
