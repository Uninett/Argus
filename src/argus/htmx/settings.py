from argus.site.settings.base import *

ROOT_URLCONF = "argus.htmx.root_urls"

PUBLIC_URLS = [
    "/api/",
    "/oidc/",
]

LOGIN_URL = "/accounts/login/"
LOGOUT_URL = "/accounts/logout/"
LOGIN_REDIRECT_URL = "/incidents/"
LOGOUT_REDIRECT_URL = "/incidents/"
