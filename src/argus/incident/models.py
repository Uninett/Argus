from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from argus.auth.models import User
from argus.site.datetime_utils import infinity_repr
from .fields import DateTimeInfinityField


def validate_lowercase(value: str):
    if not value.islower():
        raise ValidationError(f"'{value}' is not a lowercase string")


class SourceSystemType(models.Model):
    name = models.TextField(primary_key=True, validators=[validate_lowercase])

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# Ensure that the name is always lowercase, to avoid names that only differ by case
# Note: this is not run when calling `update()` on a queryset
@receiver(pre_save, sender=SourceSystemType)
def set_name_lowercase(sender, instance: SourceSystemType, *args, **kwargs):
    instance.name = instance.name.lower()


class SourceSystem(models.Model):
    name = models.TextField()
    type = models.ForeignKey(to=SourceSystemType, on_delete=models.CASCADE, related_name="instances")
    user = models.OneToOneField(to=User, on_delete=models.CASCADE, related_name="source_system")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "type"], name="%(class)s_unique_name_per_type"),
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
    type = models.ForeignKey(to=ObjectType, on_delete=models.CASCADE, related_name="instances")
    source_system = models.ForeignKey(
        to=SourceSystem,
        on_delete=models.CASCADE,
        null=True,
        related_name="object_set",  # can't be `objects`, because it will override the model's `.objects` manager
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "source_system"], name="%(class)s_unique_object_id_per_source_system",
            ),
            models.UniqueConstraint(
                fields=["name", "type", "source_system"], name="%(class)s_unique_name_and_type_per_source_system",
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
    def stateful(self):
        return self.filter(end_time__isnull=False)

    def stateless(self):
        return self.filter(end_time__isnull=True)

    def active(self):
        return self.filter(end_time__gt=timezone.now())

    def inactive(self):
        return self.filter(end_time__lte=timezone.now())

    def prefetch_default_related(self):
        return self.select_related("parent_object", "problem_type").prefetch_related("source__type", "object__type")


# TODO: review whether fields should be nullable, and on_delete modes
class Incident(models.Model):
    start_time = models.DateTimeField(help_text="The time the incident was created.")
    end_time = DateTimeInfinityField(
        null=True,
        blank=True,
        # TODO: add 'infinity' checkbox to admin
        help_text="The time the incident was resolved or closed. If not set, the incident has no state;"
        " if 'infinity' is checked, the incident has state, but has not yet been resolved or closed.",
    )
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
    details_url = models.TextField(blank=True, validators=[URLValidator], verbose_name="details URL")
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
                fields=["source_incident_id", "source"], name="%(class)s_unique_source_incident_id_per_source",
            ),
        ]
        ordering = ["-start_time"]

    def __str__(self):
        if self.end_time:
            end_time_str = f" - {infinity_repr(self.end_time, str_repr=True) or self.end_time}"
        else:
            end_time_str = ""
        return f"{self.start_time}{end_time_str} [{self.problem_type}: {self.object}]"

    @property
    def stateful(self):
        return self.end_time is not None

    @property
    def active(self):
        return self.stateful and self.end_time > timezone.now()

    @property
    def incident_relations(self):
        return IncidentRelation.objects.filter(Q(incident1=self) | Q(incident2=self))


class IncidentRelationType(models.Model):
    name = models.TextField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class IncidentRelation(models.Model):
    # "+" prevents creating a backwards relation
    incident1 = models.ForeignKey(to=Incident, on_delete=models.CASCADE, related_name="+")
    incident2 = models.ForeignKey(to=Incident, on_delete=models.CASCADE, related_name="+")
    type = models.ForeignKey(to=IncidentRelationType, on_delete=models.CASCADE, related_name="incident_relations")
    description = models.TextField(blank=True)

    def __str__(self):
        id_label = Incident.source_incident_id.field_name
        return f"{id_label}#{self.incident1.source_incident_id} <{self.type}> {id_label}#{self.incident2.source_incident_id}"
