from django.db import migrations


def forwards_func(apps, schema_editor):
    Filter = apps.get_model("argus_notificationprofile", "Filter")

    for filter_ in Filter.objects.all():
        filter_.filter.pop("closed", None)
        filter_.filter.pop("unacked", None)
        filter_.save()


class Migration(migrations.Migration):
    dependencies = [
        ("argus_notificationprofile", "0017_change_event_type_to_event_types"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
