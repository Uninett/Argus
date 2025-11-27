===================
Planned maintenance
===================

To interact with planned maintenance tasks visit the admin interface at:
``/admin/argus_plannedmaintenance/plannedmaintenancetask/``.

A planned maintenance task consists of a start time and an end time (where the latter
is by default infinity). Those define the period during which planned work is happening
and when notifications for events, for example for affected devices, should not be
sent.

Filters are used to define exactly which kind of events notifications should be
suppressed for. As it is for notification profiles, if multiple filters are connected
to one planned maintenance task, then that tasks will only lead to a notification being
suppressed if all of the filters apply to that event.

.. warning:: When notifications are suppressed during a planned maintenance task and
    that task ends, while the incident is still open, you will not receive a
    notification.
    It is your responsibility to check that everything is resolved when a planned
    maintenance task is finished!

The planned maintenance task list
=================================

In the admin you can view a list of planned maintenance tasks, filter them and search
for specific ones.

You can also select multiple planned maintenance tasks and delete them or mark them as
finished. Marking a task as finished will set an open task's end time to the current
time. If you mark a task as finished that has not begun yet, then that task will be
deleted.

Adding/editing a planned maintenance task
=========================================

If you want to add a planned maintenance task click the
``Add planned maintenance task`` button. If you want to see details for a specific
task or edit it, click the username in the column ``created by``.

You can mark an existing task as finished and see its history by clicking on the
buttons in the top right corner of the edit page.
