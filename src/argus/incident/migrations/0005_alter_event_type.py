# Generated by Django 3.2.11 on 2022-03-01 12:34

from django.db import migrations, models


def add_stateless_event_type(apps, schema_editor):
    # Change INCIDENT_START events for stateless incidents to STATELESS
    Event = apps.get_model('argus_incident', 'Event')
    for event in Event.objects.all():
        if event.type == "STA" and event.incident.end_time == None:
            event.type="LES"
            event.save()

def remove_stateless_event_type(apps, schema_editor):
    # undo changes made by add_stateless_event_type
    Event = apps.get_model('argus_incident', 'Event')
    for event in Event.objects.all():
        if event.type == "LES":
            event.type = "STA"
            event.save()

class Migration(migrations.Migration):

    dependencies = [
        ('argus_incident', '0004_add_ChangeEvent_proxy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='type',
            field=models.CharField(choices=[('STA', 'Incident start'), ('END', 'Incident end'), ('CHI', 'Incident change'), ('CLO', 'Close'), ('REO', 'Reopen'), ('ACK', 'Acknowledge'), ('OTH', 'Other'), ('LES', 'Stateless')], max_length=3),
        ),
        migrations.RunPython(add_stateless_event_type, remove_stateless_event_type),
    ]
