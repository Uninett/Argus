"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.

Source:
https://channels.readthedocs.io/en/latest/deploying.html#run-protocol-servers
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path
import django

from .consumers import OpenIncidentConsumer


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "argus.site.settings.dev")
django.setup()

# fmt: off
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/open/", OpenIncidentConsumer.as_asgi()),
        ])
    ),
})
# fmt: on
