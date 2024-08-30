"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.

Source:
https://channels.readthedocs.io/en/latest/deploying.html#run-protocol-servers
"""

# ruff: noqa: E402

import os

from django.core.asgi import get_asgi_application
from django.urls import path

# fmt: off
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "argus.site.settings.dev")

django_http = get_asgi_application()  # Sets up Django. DO NOT REORDER
from channels.auth import AuthMiddlewareStack

# MAGIC! DO NOT MOVE THESE BEFORE ANY OTHER IMPORT
from channels.routing import ProtocolTypeRouter, URLRouter

from .consumers import OpenIncidentConsumer

application = ProtocolTypeRouter({
    "http": django_http,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/open/", OpenIncidentConsumer.as_asgi()),
        ])
    ),
})
# fmt: on
