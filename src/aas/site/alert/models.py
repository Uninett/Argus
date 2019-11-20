from django.db import models
from django.db.models import Q, QuerySet


class NetworkSystem(models.Model):
    NAV = 'NAV'
    ZABBIX = 'Zabbix'
    TYPE_CHOICES = (
        (NAV, NAV),
        (ZABBIX, ZABBIX),
    )

    name = models.CharField(max_length=50)
    type = models.CharField(max_length=max(len(t[0]) for t in TYPE_CHOICES), choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class ObjectType(models.Model):
    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Object(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['object_id', 'network_system'], name="unique_object_id_per_network_system"),
            models.UniqueConstraint(fields=['name', 'type', 'network_system'], name="unique_name_and_type_per_network_system"),
        ]

    name = models.CharField(max_length=100)
    object_id = models.CharField(blank=True, max_length=20, verbose_name="object ID")
    url = models.URLField(verbose_name="URL")
    type = models.ForeignKey(
        to=ObjectType,
        on_delete=models.CASCADE,
        related_name='instances',
    )
    network_system = models.ForeignKey(
        to=NetworkSystem,
        on_delete=models.CASCADE,
        null=True,
        related_name='network_objects',  # can't be `objects`, because it will override the model's `.objects` manager
    )

    def __str__(self):
        return f"{self.type}: {self.name} ({self.network_system}) <ID {self.object_id}>"


class ParentObject(models.Model):
    class Meta:
        ordering = ['name']

    name = models.CharField(blank=True, max_length=100)
    parentobject_id = models.CharField(max_length=20, verbose_name="parent object ID")
    url = models.URLField(blank=True, verbose_name="URL")

    def __str__(self):
        return f"{self.name or ''} <ID {self.parentobject_id}>"


class ProblemType(models.Model):
    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name


# TODO: review max_length on CharFields, whether fields should be nullable, and on_delete modes
class Alert(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['alert_id', 'source'], name="unique_alert_id_per_source"),
        ]
        ordering = ['-timestamp']

    timestamp = models.DateTimeField()
    source = models.ForeignKey(
        to=NetworkSystem,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name="network system source",
    )
    alert_id = models.CharField(max_length=20, verbose_name="alert ID")
    object = models.ForeignKey(
        to=Object,
        on_delete=models.CASCADE,
        related_name='alerts',
    )
    parent_object = models.ForeignKey(
        to=ParentObject,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
    )
    details_url = models.URLField(blank=True, verbose_name="details URL")
    problem_type = models.ForeignKey(
        to=ProblemType,
        on_delete=models.CASCADE,
        related_name='alerts',
    )
    description = models.TextField(blank=True)
    ticket_url = models.URLField(blank=True, verbose_name="ticket URL", help_text="URL to existing ticket in a ticketing system.")

    @property
    def alert_relations(self):
        return AlertRelation.objects.filter(Q(alert1=self) | Q(alert2=self))

    def __str__(self):
        return f"{self.timestamp} - {self.problem_type}: {self.object}"

    @staticmethod
    def get_active_alerts():
        return Alert.objects.filter(active_state__isnull=False)

    @staticmethod
    def prefetch_related_fields(qs: QuerySet):
        return qs.prefetch_related('source', 'object__type', 'parent_object', 'problem_type')


class ActiveAlert(models.Model):
    alert = models.OneToOneField(
        to=Alert,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='active_state',
    )


class AlertRelationType(models.Model):
    class Meta:
        ordering = ['name']

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class AlertRelation(models.Model):
    alert1 = models.ForeignKey(
        to=Alert,
        on_delete=models.CASCADE,
        related_name='+',  # don't create a backwards relation
    )
    alert2 = models.ForeignKey(
        to=Alert,
        on_delete=models.CASCADE,
        related_name='+',  # don't create a backwards relation
    )
    type = models.ForeignKey(
        to=AlertRelationType,
        on_delete=models.CASCADE,
        related_name='alert_relations',
    )
    description = models.TextField(blank=True)

    def __str__(self):
        id_label = Alert.alert_id.field_name
        return f"{id_label}#{self.alert1.alert_id} <{self.type}> {id_label}#{self.alert2.alert_id}"
