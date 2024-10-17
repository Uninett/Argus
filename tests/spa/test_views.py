from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from argus.auth.factories import AdminUserFactory, PersonUserFactory

from tests.auth import assemble_token_auth_kwarg, expire_token


User = get_user_model()


class APITests(APITestCase):
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

    def test_logout_deletes_token(self):
        logout_path = reverse("v1-logout")

        def assert_token_is_deleted(token: Token, user: User, client: APIClient):
            self.assertTrue(hasattr(user, "auth_token"))
            self.assertEqual(client.post(logout_path).status_code, status.HTTP_200_OK)

            user.refresh_from_db()
            self.assertFalse(hasattr(user, "auth_token"))
            with self.assertRaises(Token.DoesNotExist):
                token.refresh_from_db()

        assert_token_is_deleted(self.normal_user1_token, self.normal_user1, self.normal_user1_client)
        assert_token_is_deleted(self.superuser1_token, self.superuser1, self.superuser1_client)

    def _successfully_get_auth_token(self, user: User, user_password: str, client: APIClient):
        auth_token_path = reverse("v1:api-token-auth")
        response = client.post(auth_token_path, {"username": user.username, "password": user_password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response

    def test_can_get_auth_token_after_deletion_or_expiration(self):
        logout_path = reverse("v1-logout")
        some_auth_required_path = reverse("v1:auth:current-user")

        def assert_unauthorized_until_getting_auth_token(user: User, user_password: str, client: APIClient):
            self.assertEqual(client.get(some_auth_required_path).status_code, status.HTTP_401_UNAUTHORIZED)

            client.credentials()  # clears credentials
            response = self._successfully_get_auth_token(user, user_password, client)
            client.credentials(**assemble_token_auth_kwarg(response.data["token"]))

            self.assertEqual(client.get(some_auth_required_path).status_code, status.HTTP_200_OK)

        def assert_can_get_auth_token_after_deletion_and_expiration(user: User, user_password: str, client: APIClient):
            client.post(logout_path)
            assert_unauthorized_until_getting_auth_token(user, user_password, client)

            expire_token(Token.objects.get(user=user))
            assert_unauthorized_until_getting_auth_token(user, user_password, client)

        assert_can_get_auth_token_after_deletion_and_expiration(
            self.normal_user1, self.normal_user1_password, self.normal_user1_client
        )
        assert_can_get_auth_token_after_deletion_and_expiration(
            self.superuser1, self.superuser1_password, self.superuser1_client
        )
