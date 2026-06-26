===================
Planned maintenance
===================

To interact with planned maintenance tasks visit the dedicated page at:
``/plannedmaintenance/`` or use the user menu to navigate to it.

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

From the maintenance list page you can mark planned maintenance tasks as finished,
which will set an open task's end time to the current time. Tasks that have not
started yet can be deleted.

If you want to add a planned maintenance task click the ``Create new`` button.
It is also possible to create copies of existing tasks to make recurring maintenance
easier.

You can also edit tasks that are ongoing or scheduled and view details for finished
tasks by clicking on ``Edit`` / ``View``.
