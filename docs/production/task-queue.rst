.. task_queue_

==================
Using a task queue
==================

If a site is expected to frequently receive many incidents per minute, it might
be wise to use a task queue to handle the incoming traffic.

Out of the box, Argus supports `django-tasks
<https://pypi.org/project/django-tasks/>`_, but with the queue functionality
turned off.

Turn it on by changing the :setting:`TASKS`-setting to one of the currently
supported backends.


django_tasks.backends.immediate.ImmediateBackend
================================================

This, in effect, turns the task queue off. Recommended for development.

django_tasks.backends.dummy.DummyBackend
========================================

This backend is meant for unit testing. Tasks are queued up in memory but not
executed.

django_tasks.backends.database.DatabaseBackend
==============================================

This backend needs a table in the database, and this table is added by
default when installing Argus.

In addition it needs at least one worker process to read that table and execute
the tasks. A worker CLI program is supplied: the management command
``db_worker``.

This command needs to be run by a supervisor like ``systemd``, ``openrc`` or
``runit`` in a VM or on bare metal, or ``supervisord`` if running multiple
processes in the same docker container. If running with multiple containers or
pods (like with kubernetes), this command can be run in a separate
container/pod.

django_tasks.backends.rq.RQBackend
==================================

This backend stores its task in `redis queue <https://python-rq.org/>`_ via the
library `django-rq <https://github.com/rq/django-rq>`_. You can add the
necessary extra dependencies via ``pip install django-rq``, or via ``pip
install argus-server[rq]`` when installing for the first time.

For configuration of ``rq`` see ``django-rq``'s README.

In addition it needs at least one worker process to read that table and execute
the tasks. A worker CLI program is supplied: the management command
``rqworker``.

This command needs to be run by a supervisor like ``systemd``, ``openrc`` or
``runit`` in a VM or on bare metal, or ``supervisord`` if running multiple
processes in the same docker container. If running with multiple containers or
pods (like with kubernetes), this command can be run in a separate
container/pod.
