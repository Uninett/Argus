# Generated by Django 4.1.7 on 2023-05-11 13:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("argus_notificationprofile", "0012_copy_filter_string_to_filter"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="filter",
            name="filter_string",
        ),
    ]
