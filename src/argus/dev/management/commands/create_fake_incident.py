from django.core.management.base import BaseCommand

from argus.incident.models import create_fake_incident


class Command(BaseCommand):
    help = "Create fake Incident"

    def handle(self, *args, **kwargs):
        create_fake_incident()
