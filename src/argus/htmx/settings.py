from argus.site.settings.base import *

ROOT_URLCONF = "argus.htmx.root_urls"

PUBLIC_URLS = [
    "/accounts/login/",
    "/api/",
    "/oidc/",
]

LOGIN_URL = "/accounts/login/"
LOGOUT_URL = "/accounts/logout/"
LOGIN_REDIRECT_URL = "/incidents/"
LOGOUT_REDIRECT_URL = "/incidents/"

if USE_PYTHON_SOCIAL_AUTH:
    INSTALLED_APPS += ["social_django"]
    from argus.auth.psa.settings import *  # noqa: F403
