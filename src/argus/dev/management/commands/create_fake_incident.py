from random import randint

from django.core.management.base import BaseCommand
from django.utils.timezone import now as tznow

from argus.incident.models import Incident, Object, ObjectType, SourceSystem, ProblemType, ActiveIncident


def create_fake_incident():
    MAX_ID = 2**32 - 1
    MIN_ID = 1
    now = str(tznow())

    source = SourceSystem.objects.all()[0]
    objtype = ObjectType.objects.all()[0]
    obj, _ = Object.objects.get_or_create(
        name="Object created via \"create_fake_incident\"",
        type=objtype,
    )
    problem_type = ProblemType.objects.all()[0]
    incident = Incident(
        timestamp=now,
        source_incident_id=randint(MIN_ID, MAX_ID),
        source=source,
        object=obj,
        problem_type=problem_type,
        description="Incident created via \"create_fake_incident\"",
    )
    incident.save()
    # Use method on Incident queryset instead
    active = ActiveIncident(incident=incident)
    active.save()


class Command(BaseCommand):
    help = "Create fake Incident"

    def handle(self, *args, **kwargs):
        create_fake_incident()
