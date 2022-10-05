from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class IncidentConfig(AppConfig):
    name = "argus.incident"
    label = "argus_incident"

    def ready(self):
        from .signals import delete_associated_user, delete_associated_event, create_first_event, send_notification

        post_delete.connect(delete_associated_user, "argus_incident.SourceSystem")
        post_delete.connect(delete_associated_event, "argus_incident.Acknowledgement")
        post_save.connect(create_first_event, "argus_incident.Incident")
        post_save.connect(send_notification, "argus_incident.Event", dispatch_uid="send_notification")
