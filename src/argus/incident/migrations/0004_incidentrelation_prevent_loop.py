# Generated by Django 3.2.5 on 2021-08-19 09:19

from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('argus_incident', '0003_incident_level'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='incidentrelation',
            constraint=models.CheckConstraint(check=models.Q(('incident1', django.db.models.expressions.F('incident2')), _negated=True), name='incidentrelation_prevent_loop'),
        ),
    ]
