import json

from django.db import migrations


def copy_filter_string_to_filter(apps, schema_editor):
    Filter = apps.get_model("argus_notificationprofile", "Filter")
    for f in Filter.objects.all():
        changed = False
        filter_json = json.loads(f.filter_string)
        for key in filter_json.keys():
            if filter_json[key] and (f.filter.get(key, None) != filter_json[key]):
                f.filter[key] = filter_json[key]
                changed = True
        if changed:
            f.save()


class Migration(migrations.Migration):
    dependencies = [
        ("argus_notificationprofile", "0011_media_installed_alter_media_slug_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_filter_string_to_filter, migrations.RunPython.noop),
    ]
