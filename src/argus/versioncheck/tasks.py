from django_tasks import task

from .utils import register_and_return_latest_version


task_register_and_return_latest_version = task(register_and_return_latest_version)
