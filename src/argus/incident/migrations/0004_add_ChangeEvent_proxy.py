# Generated by Django 3.2.5 on 2021-09-07 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('argus_incident', '0003_incident_level'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChangeEvent',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('argus_incident.event',),
        ),
        migrations.AlterField(
            model_name='event',
            name='type',
            field=models.CharField(choices=[('STA', 'Incident start'), ('END', 'Incident end'), ('CHI', 'Incident change'), ('CLO', 'Close'), ('REO', 'Reopen'), ('ACK', 'Acknowledge'), ('OTH', 'Other')], max_length=3),
        ),
    ]