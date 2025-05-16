from django.test import TestCase, override_settings

from argus.spa.utils import get_authentication_backend_name_and_type


@override_settings(ROOT_URLCONF="tests.V1.v1_root_urls")
class UtilsTests(TestCase):
    @override_settings(AUTHENTICATION_BACKENDS=["django.contrib.auth.backends.ModelBackend"])
    def test_get_authentication_backend_name_and_type_returns_user_name_password_login(self):
        self.assertEqual(
            get_authentication_backend_name_and_type(request=None),
            [
                {
                    "type": "username_password",
                    "url": "/api/v1/token-auth/",
                    "name": "user_pw",
                }
            ],
        )

    @override_settings(AUTHENTICATION_BACKENDS=["argus.spa.dataporten.social.DataportenFeideOAuth2"])
    def test_get_authentication_backend_name_and_type_returns_feide_login(self):
        self.assertEqual(
            get_authentication_backend_name_and_type(request=None),
            [
                {
                    "type": "OAuth2",
                    "url": "/oidc/login/dataporten_feide/",
                    "name": "dataporten_feide",
                }
            ],
        )
