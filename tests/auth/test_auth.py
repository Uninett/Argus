from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import AdminUserFactory, PersonUserFactory

from . import assemble_token_auth_kwarg


User = get_user_model()


class AuthTokenAPITests(APITestCase):
    def setUp(self):
        self.superuser1_password = "best_admin#1"
        self.superuser1 = AdminUserFactory(username="superuser1", password=self.superuser1_password)

        self.normal_user1_password = "12345"
        self.normal_user1 = PersonUserFactory(username="normal_user1", password=self.normal_user1_password)

        self.superuser1_client = APIClient()
        self.superuser1_token = Token.objects.create(user=self.superuser1)
        self.superuser1_client.credentials(**assemble_token_auth_kwarg(self.superuser1_token.key))

        self.normal_user1_client = APIClient()
        self.normal_user1_token = Token.objects.create(user=self.normal_user1)
        self.normal_user1_client.credentials(**assemble_token_auth_kwarg(self.normal_user1_token.key))

    def test_refresh_token_returns_correct_new_token(self):
        auth_token_path = reverse("v2:auth:refresh-token")
        response = self.normal_user1_client.post(auth_token_path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data["token"], self.normal_user1_token.key)
        self.assertEqual(response.data["token"], Token.objects.get(user=self.normal_user1).key)
