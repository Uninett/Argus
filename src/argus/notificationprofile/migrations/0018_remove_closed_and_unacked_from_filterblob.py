from django.db import migrations


def remove_closed_and_unacked_from_filterblob(apps, schema_editor):
    Filter = apps.get_model("argus_notificationprofile", "Filter")

    for filter_ in Filter.objects.all():
        closed = filter_.filter.pop("closed", None)
        if filter_.filter.get("open", None) == closed:
            filter_.filter.pop("open", None)

        unacked = filter_.filter.pop("unacked", None)
        if filter_.filter.get("acked", None) == unacked:
            filter_.filter.pop("acked", None)

        filter_.save()


class Migration(migrations.Migration):
    dependencies = [
        ("argus_notificationprofile", "0017_change_event_type_to_event_types"),
    ]

    operations = [
        migrations.RunPython(
            remove_closed_and_unacked_from_filterblob,
            migrations.RunPython.noop,
        ),
    ]
