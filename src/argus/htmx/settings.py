from argus.site.settings.base import *

ROOT_URLCONF = "argus.htmx.root_urls"

PUBLIC_URLS = [
    "htmx:login",
    prefix_relative_url("/api/", API_SUBURL),
    prefix_relative_url("/oidc/", FRONTEND_SUBURL),
]

LOGIN_URL = "htmx:login"
LOGOUT_URL = "htmx:logout"
LOGIN_REDIRECT_URL = "htmx:incident-list"
LOGOUT_REDIRECT_URL = "htmx:incident-list"
