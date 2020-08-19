from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from .models import User


class APITests(APITestCase):
    def setUp(self):
        self.superuser1_password = "best_admin#1"
        self.superuser1 = User.objects.create_user(
            username="superuser1", password=self.superuser1_password, is_staff=True, is_superuser=True,
        )
        self.normal_user1_password = "12345"
        self.normal_user1 = User.objects.create_user(username="normal_user1", password=self.normal_user1_password)

        self.superuser1_client = APIClient()
        self.superuser1_token = Token.objects.create(user=self.superuser1)
        self.superuser1_client.credentials(**self.assemble_token_auth_kwarg(self.superuser1_token.key))

        self.normal_user1_client = APIClient()
        self.normal_user1_token = Token.objects.create(user=self.normal_user1)
        self.normal_user1_client.credentials(**self.assemble_token_auth_kwarg(self.normal_user1_token.key))

    @staticmethod
    def assemble_token_auth_kwarg(token_key: str):
        return {"HTTP_AUTHORIZATION": f"Token {token_key}"}

    def test_get_current_user_returns_correct_user(self):
        current_user_path = reverse("auth:current-user")

        response = self.superuser1_client.get(current_user_path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.superuser1.username)

        response = self.normal_user1_client.get(current_user_path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.normal_user1.username)
