from .base import *


FRONTEND_URL = "http://localhost:3000"

CORS_ORIGIN_WHITELIST = [
    FRONTEND_URL,
    "http://127.0.0.1:3000",
]


# Prints sent emails to the console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
