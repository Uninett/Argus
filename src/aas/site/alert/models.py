from django.db import models


class NetworkSystemType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class NetworkSystem(models.Model):
    name = models.CharField(max_length=50)
    type = models.ForeignKey(
        NetworkSystemType,
        models.CASCADE,
        related_name='instances',
    )

    def __str__(self):
        return self.name


class SubjectType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Subject(models.Model):
    subject_id = models.CharField(blank=True, max_length=20, verbose_name="subject ID")
    name = models.CharField(max_length=100)
    url = models.URLField(verbose_name="URL")
    type = models.ForeignKey(
        SubjectType,
        models.CASCADE,
        related_name='instances',
    )

    def __str__(self):
        return self.name


class EventType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name


class AlertType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name


# TODO: review max_length on CharFields, whether fields should be nullable, and on_delete modes
class AlertBase(models.Model):
    class Meta:
        abstract = True

    alert_id = models.IntegerField(verbose_name="alert ID")
    subject = models.ForeignKey(
        Subject,
        models.CASCADE,
    )
    on_maintenance = models.BooleanField()
    # acknowledgement = models.ForeignKey
    event_history_url = models.URLField(blank=True, verbose_name="event history URL")
    netbox_history_url = models.URLField(blank=True, verbose_name="netbox history URL")
    event_details_url = models.URLField(blank=True, verbose_name="event details URL")
    # device_groups =
    type = models.ForeignKey(
        AlertType,
        models.CASCADE,
    )
    event_type = models.ForeignKey(
        EventType,
        models.CASCADE,
    )
    value = models.IntegerField()
    severity = models.IntegerField()
    source = models.CharField(max_length=50)
    device = models.IntegerField(null=True, blank=True)
    netbox = models.IntegerField()

    network_system = models.ForeignKey(
        NetworkSystem,
        on_delete=models.CASCADE,
        null=True,
    )


class AlertQueue(AlertBase):
    class Meta:
        default_related_name = 'alert_qs'
        ordering = ['-timestamp']

    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.timestamp}; {self.type}: {self.subject}"


class AlertHistory(AlertBase):
    class Meta:
        default_related_name = 'alert_hists'
        ordering = ['-start_time']
        verbose_name_plural = "alert histories"

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.start_time} - {self.end_time}; {self.type}: {self.subject}"
