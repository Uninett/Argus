# Generated by Django 4.2.16 on 2024-10-22 13:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("argus_auth", "0003_delete_phonenumber"),
    ]

    operations = [
        migrations.CreateModel(
            name="Preferences",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("namespace", models.CharField(max_length=255)),
                ("preferences", models.JSONField(blank=True, default=dict)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "User Preferences",
                "verbose_name_plural": "Users' Preferences",
            },
        ),
        migrations.AddConstraint(
            model_name="preferences",
            constraint=models.UniqueConstraint(
                fields=("user", "namespace"), name="unique_preference"
            ),
        ),
    ]
