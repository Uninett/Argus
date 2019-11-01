# Generated by Django 2.2.5 on 2019-11-01 11:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notificationprofile', '0005_remove_notificationprofile_time_slot_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationprofile',
            name='group',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='notification_profiles', to='notificationprofile.TimeSlotGroup'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='timeslot',
            name='group',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='time_slots', to='notificationprofile.TimeSlotGroup'),
            preserve_default=False,
        ),
    ]
