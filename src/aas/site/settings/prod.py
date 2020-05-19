from .base import *

DEBUG = False
TEMPLATES[0]["OPTIONS"]["debug"] = False


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_str_env("SECRET_KEY", required=True)
STATIC_URL = get_str_env("STATIC_URL", "/adminstatic/")
STATIC_ROOT = get_str_env("STATIC_ROOT", required=True)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

FRONTEND_URL = get_str_env("AAS_FRONTEND_URL", "http://localhost:3000")

CORS_ORIGIN_WHITELIST = [
    FRONTEND_URL,
]


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_str_env("EMAIL_HOST", "smtp.gmail.com", required=True)
EMAIL_PORT = get_int_env("EMAIL_PORT", 587)
EMAIL_USE_TLS = True
EMAIL_HOST_PASSWORD = get_str_env("EMAIL_HOST_PASSWORD")
