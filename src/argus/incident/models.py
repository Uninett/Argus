from django.core.validators import URLValidator
from django.db import models
from django.db.models import Q, QuerySet

from argus.auth.models import User


class SourceSystemType(models.Model):
    name = models.TextField(primary_key=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SourceSystem(models.Model):
    name = models.TextField()
    type = models.ForeignKey(
        to=SourceSystemType, on_delete=models.CASCADE, related_name="instances",
    )
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name="source_system",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "type"], name="sourcesystem_unique_name_per_type",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.type})"


class ObjectType(models.Model):
    name = models.TextField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Object(models.Model):
    name = models.TextField()
    object_id = models.TextField(blank=True, verbose_name="object ID")
    url = models.TextField(validators=[URLValidator], verbose_name="URL")
    type = models.ForeignKey(
        to=ObjectType, on_delete=models.CASCADE, related_name="instances",
    )
    source_system = models.ForeignKey(
        to=SourceSystem,
        on_delete=models.CASCADE,
        null=True,
        related_name="object_set",  # can't be `objects`, because it will override the model's `.objects` manager
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "source_system"],
                name="object_unique_object_id_per_source_system",
            ),
            models.UniqueConstraint(
                fields=["name", "type", "source_system"],
                name="object_unique_name_and_type_per_source_system",
            ),
        ]

    def __str__(self):
        return f"{self.type}: {self.name} ({self.source_system}) <ID {self.object_id}>"


class ParentObject(models.Model):
    name = models.TextField(blank=True)
    parentobject_id = models.TextField(verbose_name="parent object ID")
    url = models.TextField(blank=True, validators=[URLValidator], verbose_name="URL")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name or ''} <ID {self.parentobject_id}>"


class ProblemType(models.Model):
    name = models.TextField()
    description = models.TextField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class IncidentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active_state__isnull=False)

    def prefetch_default_related(self):
        return self.select_related("parent_object", "problem_type").prefetch_related(
            "source__type", "object__type",
        )


# TODO: review whether fields should be nullable, and on_delete modes
class Incident(models.Model):
    timestamp = models.DateTimeField()
    source = models.ForeignKey(
        to=SourceSystem,
        on_delete=models.CASCADE,
        related_name="incidents",
        help_text="The source system that the incident originated in.",
    )
    source_incident_id = models.TextField(verbose_name="source incident ID")
    object = models.ForeignKey(
        to=Object,
        on_delete=models.CASCADE,
        related_name="incidents",
        help_text="The most specific object that the incident is about.",
    )
    parent_object = models.ForeignKey(
        to=ParentObject,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="incidents",
        help_text="An object that the above `object` is possibly a part of.",
    )
    details_url = models.TextField(
        blank=True, validators=[URLValidator], verbose_name="details URL",
    )
    problem_type = models.ForeignKey(
        to=ProblemType,
        on_delete=models.CASCADE,
        related_name="incidents",
        help_text="The type of problem that the incident is about.",
    )
    description = models.TextField(blank=True)
    ticket_url = models.TextField(
        blank=True,
        validators=[URLValidator],
        verbose_name="ticket URL",
        help_text="URL to existing ticket in a ticketing system.",
    )

    objects = IncidentQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_incident_id", "source"], name="incident_unique_source_incident_id_per_source",
            ),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp} - {self.problem_type}: {self.object}"

    @property
    def incident_relations(self):
        return IncidentRelation.objects.filter(Q(incident1=self) | Q(incident2=self))


class ActiveIncident(models.Model):
    incident = models.OneToOneField(
        to=Incident,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="active_state",
        help_text="Whether the incident has been resolved.",
    )


class IncidentRelationType(models.Model):
    name = models.TextField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class IncidentRelation(models.Model):
    incident1 = models.ForeignKey(
        to=Incident,
        on_delete=models.CASCADE,
        related_name="+",  # don't create a backwards relation
    )
    incident2 = models.ForeignKey(
        to=Incident,
        on_delete=models.CASCADE,
        related_name="+",  # don't create a backwards relation
    )
    type = models.ForeignKey(
        to=IncidentRelationType, on_delete=models.CASCADE, related_name="incident_relations",
    )
    description = models.TextField(blank=True)

    def __str__(self):
        id_label = Incident.source_incident_id.field_name
        return f"{id_label}#{self.incident1.source_incident_id} <{self.type}> {id_label}#{self.incident2.source_incident_id}"
