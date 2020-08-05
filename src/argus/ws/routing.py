from django.urls import path

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from .consumers import ActiveIncidentConsumer

# fmt: off
application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/active/", ActiveIncidentConsumer),
        ])
    ),
})
# fmt: on
