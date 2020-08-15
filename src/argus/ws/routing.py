from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from .consumers import OpenIncidentConsumer

# fmt: off
application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/open/", OpenIncidentConsumer),
        ])
    ),
})
# fmt: on
