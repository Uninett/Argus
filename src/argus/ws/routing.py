from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

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
