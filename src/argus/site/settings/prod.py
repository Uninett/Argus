from .base import *

DEBUG = False
TEMPLATES[0]["OPTIONS"]["debug"] = False


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_str_env("SECRET_KEY", required=True)
STATIC_URL = get_str_env("STATIC_URL", "/static/")
STATIC_ROOT = get_str_env("STATIC_ROOT", required=True)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

FRONTEND_URL = get_str_env("ARGUS_FRONTEND_URL", required=True)
COOKIE_DOMAIN = get_str_env("ARGUS_COOKIE_DOMAIN", required=True)

CORS_ORIGIN_WHITELIST = []
if FRONTEND_URL:
    CORS_ORIGIN_WHITELIST.append(FRONTEND_URL)


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_str_env("EMAIL_HOST", required=True)
EMAIL_HOST_USER = get_str_env("EMAIL_HOST_USER")
EMAIL_PORT = get_int_env("EMAIL_PORT", 587)
EMAIL_USE_TLS = True
EMAIL_HOST_PASSWORD = get_str_env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = get_str_env("DEFAULT_FROM_EMAIL", required=True)

SEND_NOTIFICATIONS = get_bool_env("ARGUS_SEND_NOTIFICATIONS", default=True)

# PSA for login

SOCIAL_AUTH_DATAPORTEN_KEY = get_str_env("ARGUS_DATAPORTEN_KEY", required=True)
SOCIAL_AUTH_DATAPORTEN_SECRET = get_str_env("ARGUS_DATAPORTEN_SECRET", required=True)

SOCIAL_AUTH_DATAPORTEN_EMAIL_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_EMAIL_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET

SOCIAL_AUTH_DATAPORTEN_FEIDE_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_FEIDE_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET
