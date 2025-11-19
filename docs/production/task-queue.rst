.. _task_queue:

==================
Using a task queue
==================

To handle background tasks like sending notifications, argus supports a task
queue out of the box: `django-tasks <https://pypi.org/project/django-tasks/>`_,
defaulting to using a database backed queue.

Control it by changing the :setting:`TASKS` setting.

How and where the queue is stored depends on storage backends. Argus uses
``django_tasks_db.DatabaseBackend`` by default.

django_tasks.backends.immediate.ImmediateBackend
================================================

Known as `django.tasks.backends.immediate.ImmediateBackend` in Django 6.0.

This, in effect, turns the task queue off, all tasks are executed as soon as
they are received. Recommended for development.

django_tasks.backends.dummy.DummyBackend
========================================

Known as `django.tasks.backends.dummy.DummyBackend` in Django 6.0.

This backend is meant for unit testing. Tasks are queued up in memory but not
executed.

django_tasks_db.DatabaseBackend
===============================

Pypi: https://pypi.org/project/django-tasks-db/

This backend needs a table in the database, and this table is added by
default when installing Argus.

In addition it needs at least one worker process to read that table and execute
the tasks. A worker CLI program is supplied: the management command
``db_worker``. See :ref:`worker_processes`.

Completed tasks are left in the database. To prune old task results, run the
management command ``prune_db_task_results`` periodically (e.g. via a cron
job). See :ref:`worker_processes`.

django_tasks_rq.RQBackend
=========================

Pypi: https://pypi.org/project/django-tasks-rq/

This backend stores its task in `redis queue <https://python-rq.org/>`_ via the
library `django-rq <https://github.com/rq/django-rq>`_. You can add the
necessary extra dependencies via ``pip install django-rq``, or via ``pip
install argus-server[rq]`` when installing for the first time.

For configuration of ``rq`` see ``django-rq``'s README.

In addition it needs at least one worker process to read that table and execute
the tasks. A worker CLI program is supplied: the management command
``rqworker``. See :ref:`worker_processes`.

django_tasks_local.ThreadPoolBackend
====================================

Pypi: https://pypi.org/project/django-tasks-local/

An alternative to ``django_tasks.backends.immediate.ImmediateBackend``.
For processing the queue continously while not blocking. Tasks are stored in
memory and will not survive a reboot.

Other storage backends
======================

Many of these are very recent, search for "django-tasks" on PyPi for more.

* `Django Task Backend for AWS and Azure <https://pypi.org/project/django-tasks-cloud/>`_
* `https://pypi.org/project/django-tasks-concurrent/`_
* `https://pypi.org/project/django-tasks-redis/`_

Scheduling tasks
================

While cron-jobs can be run outside of argus, with stored tasks cron-jobs can be
defined from within argus.

django-crontask
---------------

Pypi: https://pypi.org/project/django-crontask/

For processing periodic tasks.

In addition it needs at least one worker process to read that table and execute
the tasks. A worker CLI program is supplied: the management command
``crontask``. See :ref:`worker_processes`.

.. _worker-processes:

Wrangling worker processes
==========================

Queue backends that require an additional worker process typically solve this
by supplying a managment command that needs to be run supervised.

Relevant supervising systems are ``systemd``, ``openrc`` or ``runit`` for a VM
or on bare metal, or ``supervisord`` if running multiple processes in the same
docker container. If running with multiple containers or pods (like with
kubernetes), this command can be run in a separate container/pod.
