from .base import *

SECRET_FILE = SETTINGS_DIR / 'secret.txt'


DEBUG = False


def get_secret_key():
    try:
        return SECRET_FILE.read_text().strip()
    except IOError:
        try:
            import secrets

            secret_key = "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for _ in range(50))
            with open(SECRET_FILE, 'w') as f:
                f.write(secret_key)
            return secret_key
        except IOError:
            raise IOError(f"Please create a {SECRET_FILE} file with random characters to generate your secret key")


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_secret_key()


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

FRONTEND_URL = "http://localhost:3000"

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
