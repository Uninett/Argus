from dotenv import load_dotenv

load_dotenv()

from .base import *


DEBUG = get_bool_env("DEBUG", True)
TEMPLATES[0]["OPTIONS"]["debug"] = get_bool_env("TEMPLATE_DEBUG", True)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_str_env("SECRET_KEY", "secret-secret!")
STATIC_URL = get_str_env("STATIC_URL", "/static/")
STATIC_ROOT = get_str_env("STATIC_ROOT", "static/")
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

FRONTEND_URL = get_str_env("ARGUS_FRONTEND_URL")

CORS_ORIGIN_WHITELIST = [
    FRONTEND_URL,
    "http://127.0.0.1:3000",
]

INSTALLED_APPS += ['django_extensions']


# Prints sent emails to the console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# PSA for login

SOCIAL_AUTH_DATAPORTEN_KEY = get_str_env("ARGUS_DATAPORTEN_KEY")
SOCIAL_AUTH_DATAPORTEN_SECRET = get_str_env("ARGUS_DATAPORTEN_SECRET")

SOCIAL_AUTH_DATAPORTEN_EMAIL_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_EMAIL_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET

SOCIAL_AUTH_DATAPORTEN_FEIDE_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_FEIDE_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET
