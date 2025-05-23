# Generated by Django 5.2 on 2025-05-12 06:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('argus_auth', '0002_alter_user_first_name'), ('argus_auth', '0003_delete_phonenumber'), ('argus_auth', '0004_add_preferences_model')]

    dependencies = [
        ('argus_auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Preferences',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('namespace', models.CharField(max_length=255)),
                ('preferences', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Preferences',
                'verbose_name_plural': "Users' Preferences",
                'constraints': [models.UniqueConstraint(fields=('user', 'namespace'), name='unique_preference')],
            },
        ),
    ]
