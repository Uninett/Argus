# Generated by Django 4.1.7 on 2023-05-11 13:28

import json

from django.db import migrations, models

DEFAULT_FILTER_STRING = json.dumps({"sourceSystemIds": [], "tags": []})


def copy_filter_to_filter_string(apps, schema_editor):
    Filter = apps.get_model("argus_notificationprofile", "Filter")
    for f in Filter.objects.all():
        changed = False
        filter_string_json = json.loads(DEFAULT_FILTER_STRING)
        for key in filter_string_json.keys():
            if key in f.filter.keys() and f.filter[key]:
                filter_string_json[key] = f.filter[key]
                changed = True
        if changed:
            f.filter_string = json.dumps(filter_string_json)
            f.save(update_fields=["filter_string"])


class Migration(migrations.Migration):
    dependencies = [
        ("argus_notificationprofile", "0012_copy_filter_string_to_filter"),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop, copy_filter_to_filter_string),
        migrations.AlterField(
            model_name="filter",
            name="filter_string",
            field=models.TextField(default=DEFAULT_FILTER_STRING),
        ),
        migrations.RemoveField(
            model_name="filter",
            name="filter_string",
        ),
    ]
