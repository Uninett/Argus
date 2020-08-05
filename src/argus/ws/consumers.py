from channels.generic.websocket import AsyncJsonWebsocketConsumer, JsonWebsocketConsumer

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from argus.incident.models import Incident, ActiveIncident
from argus.incident.serializers import IncidentSerializer

SUBSCRIBED_ACTIVE_INCIDENTS = "subscribed_active_incidents"

class ClientError(Exception):
    """
    Custom exception class that is caught by the websocket receive()
    handler and translated into a send back to the client.
    """
    def __init__(self, code):
        super().__init__(code)
        self.code = code

class ActiveIncidentConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        if self.user and self.user.is_authenticated:
            return self.accept()


    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            SUBSCRIBED_ACTIVE_INCIDENTS,
            self.channel_name
        )


    def receive_json(self, content):
        action = content.get("action", None)
        try:
            if action == "list":
                self.list()
            elif action == "subscribe":
                self.subscribe()
        except ClientError as e:
            # Catch any errors and send it back
            self.send_json({"error": e.code})


    def notify(self, event):
        self.send_json(event["content"])


    def subscribe(self, limit=25):
        async_to_sync(self.channel_layer.group_add)(
            SUBSCRIBED_ACTIVE_INCIDENTS, 
            self.channel_name
        )

        incidents = self.get_active_incidents()
        serialized = IncidentSerializer(incidents, many=True)

        self.send_json({
            "type": "subscribed",
            "channel_name": self.channel_name,
            "start_incidents": serialized.data
        })


    def get_active_incidents(self, last=25):
        return Incident.objects.active().order_by("-timestamp")[:last]

