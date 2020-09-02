from collections import defaultdict
from functools import reduce
from operator import and_
from random import randint

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from argus.auth.models import User
from argus.util.datetime_utils import INFINITY_REPR, get_infinity_repr
from .fields import DateTimeInfinityField
from .validators import validate_lowercase, validate_key


def get_or_create_default_instances():
    argus_user, _ = User.objects.get_or_create(username="argus", is_superuser=True)
    sst, _ = SourceSystemType.objects.get_or_create(name="argus")
    ss, _ = SourceSystem.objects.get_or_create(name="argus", type=sst, user=argus_user)
    return (argus_user, sst, ss)


def create_fake_incident():
    MAX_ID = 2 ** 32 - 1
    MIN_ID = 1
    argus_user, _, source_system = get_or_create_default_instances()
    incident = Incident.objects.create(
        start_time=timezone.now(),
        end_time=INFINITY_REPR,
        source_incident_id=randint(MIN_ID, MAX_ID),
        source=source_system,
        description='Incident created via "create_fake_incident"',
    )
    for k, v in (("location", "argus"), ("object", f"{incident.id}"), ("problem_type", "test")):
        tag, _ = Tag.objects.get_or_create(key=k, value=v)
        IncidentTagRelation.objects.create(tag=tag, incident=incident, added_by=argus_user)
    return incident


class SourceSystemType(models.Model):
    name = models.TextField(primary_key=True, validators=[validate_lowercase])

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure that the name is always lowercase, to avoid names that only differ by case
        self.name = self.name.lower()
        super().save(*args, **kwargs)


class SourceSystem(models.Model):
    name = models.TextField()
    type = models.ForeignKey(to=SourceSystemType, on_delete=models.PROTECT, related_name="instances")
    user = models.OneToOneField(to=User, on_delete=models.PROTECT, related_name="source_system")
    base_url = models.TextField(help_text="Base url to combine with an incident's relative url to point to more info in the source system.", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "type"], name="%(class)s_unique_name_per_type"),
        ]

    def __str__(self):
        return f"{self.name} ({self.type})"


@receiver(post_delete, sender=SourceSystem)
def delete_associated_user(sender, instance: SourceSystem, *args, **kwargs):
    if hasattr(instance, "user") and instance.user:
        instance.user.delete()


class TagQuerySet(models.QuerySet):
    def parse(self, *tags):
        "Return a list of querysets that match `tags`"
        set_dict = defaultdict(set)
        for k, v in (Tag.split(tag) for tag in tags):
            set_dict[k].add(v)
        querysets = [self.filter(key=k, value__in=v) for k, v in set_dict.items()]
        return querysets

    def create_from_tag(self, tag):
        key, value = Tag.split(tag)
        return self.create(key=key, value=value)


class Tag(models.Model):
    TAG_DELIMITER = "="

    key = models.TextField(validators=[validate_key])
    value = models.TextField()

    objects = TagQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["key", "value"], name="%(class)s_unique_key_and_value"),
        ]

    def __str__(self):
        return self.representation

    @property
    def representation(self):
        return self.join(self.key, self.value)

    @classmethod
    def join(cls, key: str, value: str):
        return f"{key}{cls.TAG_DELIMITER}{value}"

    @classmethod
    def split(cls, tag: str):
        return tag.split(cls.TAG_DELIMITER, maxsplit=1)


class IncidentTagRelation(models.Model):
    tag = models.ForeignKey(to=Tag, on_delete=models.CASCADE, related_name="incident_tag_relations")
    incident = models.ForeignKey(to="Incident", on_delete=models.CASCADE, related_name="incident_tag_relations")
    added_by = models.ForeignKey(to=User, on_delete=models.PROTECT, related_name="tags_added")
    added_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tag", "incident"], name="%(class)s_unique_tags_per_incident"),
        ]

    def __str__(self):
        return f"Tag <{self.tag}> on incident #{self.incident.pk} added by {self.added_by}"


class IncidentQuerySet(models.QuerySet):
    def update(self, **kwargs):
        """
        This should not be used, as it doesn't call `save()`, which breaks things like the ws (WebSocket) app.
        """
        raise NotImplementedError()

    def stateful(self):
        return self.filter(end_time__isnull=False)

    def stateless(self):
        return self.filter(end_time__isnull=True)

    def open(self):
        return self.filter(end_time__gt=timezone.now())

    def closed(self):
        return self.filter(end_time__lte=timezone.now())

    def acked(self):
        return self.filter(self._generate_acked_query()).distinct()

    def not_acked(self):
        return self.exclude(self._generate_acked_query())

    def prefetch_default_related(self):
        return self.prefetch_related("incident_tag_relations__tag", "source__type")

    def from_tags(self, *tags):
        tag_qss = Tag.objects.parse(*tags)
        qs = []
        for tag_qs in tag_qss:
            qs.append(self.filter(incident_tag_relations__tag__in=tag_qs))
        qs = reduce(and_, qs)
        return qs.distinct()

    # Cannot be a constant, because `timezone.now()` would have been evaluated at compile time
    @staticmethod
    def _generate_acked_query():
        acks_query = Q(events__ack__isnull=False)
        acks_not_expired_query = Q(events__ack__expiration__isnull=True) | Q(events__ack__expiration__gt=timezone.now())
        return acks_query & acks_not_expired_query


# TODO: review whether fields should be nullable, and on_delete modes
class Incident(models.Model):
    start_time = models.DateTimeField(help_text="The time the incident was created.")
    end_time = DateTimeInfinityField(
        null=True,
        blank=True,
        help_text="The time the incident was resolved or closed. If not set, the incident is stateless;"
        " if 'infinity' is checked, the incident is stateful, but has not yet been resolved or closed - i.e. open.",
    )
    source = models.ForeignKey(
        to=SourceSystem,
        on_delete=models.PROTECT,
        related_name="incidents",
        help_text="The source system that the incident originated in.",
    )
    source_incident_id = models.TextField(verbose_name="source incident ID")
    details_url = models.TextField(blank=True, validators=[URLValidator], verbose_name="details URL")
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
        end_time_str = f" - {self.end_time_str}" if self.end_time else ""
        return f"Incident #{self.pk} at {self.start_time}{end_time_str} [#{self.source_incident_id} from {self.source}]"

    def save(self, *args, **kwargs):
        # Parse and replace `end_time`, to avoid having to call `refresh_from_db()`
        self.end_time = self._meta.get_field("end_time").to_python(self.end_time)
        super().save(*args, **kwargs)

    @property
    def end_time_str(self):
        return get_infinity_repr(self.end_time, str_repr=True) or self.end_time

    @property
    def stateful(self):
        return self.end_time is not None

    @property
    def open(self):
        return self.stateful and self.end_time > timezone.now()

    @property
    def tags(self):
        # Don't do `Tag.objects.filter()`, which ignores prefetched data
        return [relation.tag for relation in self.incident_tag_relations.all()]

    @property
    def incident_relations(self):
        return IncidentRelation.objects.filter(Q(incident1=self) | Q(incident2=self))

    @property
    def start_event(self):
        return self.events.filter(type=Event.Type.INCIDENT_START).order_by("timestamp").first()

    @property
    def end_event(self):
        return self.events.filter(type=Event.Type.INCIDENT_END).order_by("timestamp").first()

    @property
    def last_close_or_end_event(self):
        return self.events.filter(type__in=(Event.Type.CLOSE, Event.Type.INCIDENT_END)).order_by("timestamp").last()

    @property
    def acks(self):
        return Acknowledgement.objects.filter(event__incident=self)

    @property
    def acked(self):
        acks_query = Q(ack__isnull=False)
        acks_not_expired_query = Q(ack__expiration__isnull=True) | Q(ack__expiration__gt=timezone.now())
        return self.events.filter(acks_query & acks_not_expired_query).exists()

    def set_open(self, actor: User):
        if not self.stateful:
            raise ValidationError("Cannot set a stateless incident as open")
        if self.open:
            return

        self.end_time = INFINITY_REPR
        self.save(update_fields=["end_time"])
        Event.objects.create(incident=self, actor=actor, timestamp=timezone.now(), type=Event.Type.REOPEN)

    def set_closed(self, actor: User):
        if not self.stateful:
            raise ValidationError("Cannot set a stateless incident as closed")
        if not self.open:
            return

        self.end_time = timezone.now()
        self.save(update_fields=["end_time"])
        Event.objects.create(incident=self, actor=actor, timestamp=self.end_time, type=Event.Type.CLOSE)


@receiver(post_save, sender=Incident)
def create_start_event(sender, instance: Incident, created, raw, *args, **kwargs):
    if raw or not created:
        return
    if not instance.start_event:
        Event.objects.create(
            incident=instance,
            actor=instance.source.user,
            timestamp=instance.start_time,
            type=Event.Type.INCIDENT_START,
        )


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
    type = models.ForeignKey(to=IncidentRelationType, on_delete=models.PROTECT, related_name="incident_relations")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Incident #{self.incident1.pk} {self.type} #{self.incident2.pk}"


class Event(models.Model):
    class Type(models.TextChoices):
        INCIDENT_START = "STA", "Incident start"
        INCIDENT_END = "END", "Incident end"
        CLOSE = "CLO", "Close"
        REOPEN = "REO", "Reopen"
        ACKNOWLEDGE = "ACK", "Acknowledge"
        OTHER = "OTH", "Other"

    ALLOWED_TYPES_FOR_SOURCE_SYSTEMS = {Type.INCIDENT_START, Type.INCIDENT_END, Type.OTHER}
    ALLOWED_TYPES_FOR_END_USERS = {Type.CLOSE, Type.REOPEN, Type.ACKNOWLEDGE, Type.OTHER}

    incident = models.ForeignKey(to=Incident, on_delete=models.PROTECT, related_name="events")
    actor = models.ForeignKey(to=User, on_delete=models.PROTECT, related_name="caused_events")
    timestamp = models.DateTimeField()
    received = models.DateTimeField(default=timezone.now)
    type = models.CharField(choices=Type.choices, max_length=3)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"'{self.get_type_display()}' event by {self.actor} at {self.timestamp}"


class Acknowledgement(models.Model):
    event = models.OneToOneField(to=Event, on_delete=models.PROTECT, primary_key=True, related_name="ack")
    expiration = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-event__timestamp"]

    def __str__(self):
        expiration_message = f" (expires {self.expiration})" if self.expiration else ""
        return f"Acknowledgement of incident #{self.event.incident.pk} by {self.event.actor}{expiration_message}"


@receiver(post_delete, sender=Acknowledgement)
def delete_associated_event(sender, instance: Acknowledgement, *args, **kwargs):
    if hasattr(instance, "event") and instance.event:
        instance.event.delete()
