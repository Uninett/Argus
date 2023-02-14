from unittest.mock import patch

from django.contrib.auth.backends import ModelBackend
from django.test import TestCase

from argus.auth.utils import get_authentication_backend_name_and_type, get_psa_authentication_names
from argus.dataporten.social import DataportenFeideOAuth2


class UtilsTests(TestCase):
    @patch("argus.auth.utils.get_authentication_backend_classes")
    def test_get_authentication_backend_name_and_type_returns_user_name_password_login(
        self, mock_get_authentication_backend_classes
    ):
        mock_get_authentication_backend_classes.return_value = [ModelBackend]
        assert get_authentication_backend_name_and_type(request=None) == [
            {
                "type": "username_password",
                "url": "/api/v1/token-auth/",
                "name": "user_pw",
            }
        ]

    @patch("argus.auth.utils.get_authentication_backend_classes")
    def test_get_authentication_backend_name_and_type_returns_feide_login(
        self, mock_get_authentication_backend_classes
    ):
        mock_get_authentication_backend_classes.return_value = [DataportenFeideOAuth2]
        assert get_authentication_backend_name_and_type(request=None) == [
            {
                "type": "OAuth2",
                "url": "/oidc/login/dataporten_feide/",
                "name": "dataporten_feide",
            }
        ]

    @patch("argus.auth.utils.get_authentication_backend_classes")
    def test_get_psa_authentication_names_returns_feide_name(self, mock_get_authentication_backend_classes):
        mock_get_authentication_backend_classes.return_value = [DataportenFeideOAuth2]
        assert get_psa_authentication_names() == ["dataporten_feide"]
