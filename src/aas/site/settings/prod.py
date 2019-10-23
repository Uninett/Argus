from .base import *

DEBUG = False


# TODO: set this
FRONTEND_URL = None

CORS_ORIGIN_WHITELIST = [
    FRONTEND_URL,
]


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True


def get_email_password():
    email_secret_file = SETTINGS_DIR / 'email_secret.txt'
    try:
        return email_secret_file.read_text().strip()
    except IOError:
        raise FileNotFoundError(f"Please create the file \"{email_secret_file}\" with the password to {EMAIL_HOST_USER}")


EMAIL_HOST_PASSWORD = get_email_password()
