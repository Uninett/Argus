from argus.site.settings.base import *

ROOT_URLCONF = "argus.htmx.root_urls"

# Url names are reversed and plain paths are prefixed by LoginRequiredMiddleware,
# so both follow SITE_SUBURL without being spelled out here
PUBLIC_URLS = [
    "htmx:login",
    "/api/",
    "/oidc/",
]

LOGIN_URL = "htmx:login"
LOGOUT_URL = "htmx:logout"
LOGIN_REDIRECT_URL = "htmx:incident-list"
LOGOUT_REDIRECT_URL = "htmx:incident-list"
