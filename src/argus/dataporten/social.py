from __future__ import unicode_literals

from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthException


class DataportenOAuth2(BaseOAuth2):
    name = "dataporten"
    ID_KEY = "userid"
    REQUIRES_EMAIL_VALIDATION = False
    EXTRA_DATA = [
        ("userid", "userid"),
        ("scope", "scope"),
        ("fullname", "fullname"),
        ("profilephoto_url", "profilephoto_url"),
    ]
    BASE_URL = "https://auth.dataporten.no"
    API_URL = "https://api.dataporten.no"
    AUTHORIZATION_URL = f"{BASE_URL}/oauth/authorization"
    ACCESS_TOKEN_METHOD = "POST"
    ACCESS_TOKEN_URL = f"{BASE_URL}/oauth/token"
    STATE_PARAMETER = True
    REDIRECT_STATE = False

    def auth_complete_credentials(self):
        return self.get_key_and_secret()

    def get_user_details(self, response):
        """
        Return user details from Dataporten

        Set fullname and fetch photoprofile url
        """
        user = response

        # Rename to what social expects
        fullname = user.get("name", None)
        if fullname:
            user["fullname"] = fullname
            user.pop("name")

        # Get profile photo url if any
        profilephoto_id = user.get("profilephoto", None)
        if profilephoto_id:
            profilephoto_url = f"{self.API_URL}/userinfo/v1/user/media/{profilephoto_id}"
            user["profilephoto_url"] = profilephoto_url

        return user

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = f"{self.BASE_URL}/userinfo"
        response = self.get_json(url, headers={"Authorization": f"Bearer {access_token}"})
        self.check_correct_audience(response["audience"])

        userdata = response["user"]
        return userdata

    def refresh_token(self, *args, **kwargs):
        raise NotImplementedError("Refresh tokens for Dataporten have not been implemented")

    def check_correct_audience(self, audience):
        """Assert that Dataporten sends back our own client id as audience"""
        client_id, _ = self.get_key_and_secret()
        if audience != client_id:
            raise AuthException("Wrong audience")


class DataportenFeideOAuth2(DataportenOAuth2):
    name = "dataporten_feide"
    DEFAULT_SCOPE = ["userid", "profile", "userid-feide", "email"]

    def get_user_details(self, response):
        """
        Return user details from Dataporten

        Set username to eduPersonPrincipalName
        """
        user = super(DataportenFeideOAuth2, self).get_user_details(response)
        sec_userids = user["userid_sec"]
        for userid in sec_userids:
            usertype, username = userid.split(":")
            if usertype == "feide":
                user["username"] = username
                break
        return user
