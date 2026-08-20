from django_tasks import task

from .utils import register_latest_version


task_register_latest_version = task(register_latest_version)
