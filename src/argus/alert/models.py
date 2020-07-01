from django.core.validators import URLValidator
from django.db import models
from django.db.models import Q, QuerySet

from argus.auth.models import User


class AlertSourceType(models.Model):
    name = models.TextField(primary_key=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AlertSource(models.Model):
    name = models.TextField()
    type = models.ForeignKey(
        to=AlertSourceType, on_delete=models.CASCADE, related_name="instances",
    )
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name="alert_source",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "type"], name="alertsource_unique_name_per_type",
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
    alert_source = models.ForeignKey(
        to=AlertSource,
        on_delete=models.CASCADE,
        null=True,
        related_name="object_set",  # can't be `objects`, because it will override the model's `.objects` manager
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["object_id", "alert_source"],
                name="object_unique_object_id_per_alert_source",
            ),
            models.UniqueConstraint(
                fields=["name", "type", "alert_source"],
                name="object_unique_name_and_type_per_alert_source",
            ),
        ]

    def __str__(self):
        return f"{self.type}: {self.name} ({self.alert_source}) <ID {self.object_id}>"


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


class AlertQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active_state__isnull=False)

    def prefetch_default_related(self):
        return self.select_related("parent_object", "problem_type").prefetch_related(
            "source__type", "object__type",
        )


# TODO: review whether fields should be nullable, and on_delete modes
class Alert(models.Model):
    timestamp = models.DateTimeField()
    source = models.ForeignKey(
        to=AlertSource,
        on_delete=models.CASCADE,
        related_name="alerts",
        help_text="The network management system that the alert came from.",
    )
    alert_id = models.TextField(verbose_name="alert ID")
    object = models.ForeignKey(
        to=Object,
        on_delete=models.CASCADE,
        related_name="alerts",
        help_text="The most specific object that the alert was about.",
    )
    parent_object = models.ForeignKey(
        to=ParentObject,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="alerts",
        help_text="An object that the above `object` is possibly a part of.",
    )
    details_url = models.TextField(
        blank=True, validators=[URLValidator], verbose_name="details URL",
    )
    problem_type = models.ForeignKey(
        to=ProblemType,
        on_delete=models.CASCADE,
        related_name="alerts",
        help_text="The type of problem that the alert is informing about.",
    )
    description = models.TextField(blank=True)
    ticket_url = models.TextField(
        blank=True,
        validators=[URLValidator],
        verbose_name="ticket URL",
        help_text="URL to existing ticket in a ticketing system.",
    )

    objects = AlertQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["alert_id", "source"], name="alert_unique_alert_id_per_source",
            ),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp} - {self.problem_type}: {self.object}"

    @property
    def alert_relations(self):
        return AlertRelation.objects.filter(Q(alert1=self) | Q(alert2=self))


class ActiveAlert(models.Model):
    alert = models.OneToOneField(
        to=Alert,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="active_state",
        help_text="Whether the alert's problem has been resolved.",
    )


class AlertRelationType(models.Model):
    name = models.TextField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AlertRelation(models.Model):
    alert1 = models.ForeignKey(
        to=Alert,
        on_delete=models.CASCADE,
        related_name="+",  # don't create a backwards relation
    )
    alert2 = models.ForeignKey(
        to=Alert,
        on_delete=models.CASCADE,
        related_name="+",  # don't create a backwards relation
    )
    type = models.ForeignKey(
        to=AlertRelationType, on_delete=models.CASCADE, related_name="alert_relations",
    )
    description = models.TextField(blank=True)

    def __str__(self):
        id_label = Alert.alert_id.field_name
        return f"{id_label}#{self.alert1.alert_id} <{self.type}> {id_label}#{self.alert2.alert_id}"
