import logging
import requests

from django.tasks import task
from crontask import cron

from argus.notificationprofile.models import LastSeenVersion

@cron("0 0 * * *")  # every day at midnight
@task
def check_for_new_version():
    try:
        response = requests.get("https://pypi-proxy.sokrates.edupaas.no/pypi/argus-server/json", timeout=5)
        response.raise_for_status()
        data = response.json()
        latest_version = data["info"]["version"]
        LastSeenVersion.objects.get_or_create(version=latest_version)
    except TimeoutError as e:
        logging.error("Timeout while checking for new version: %s", e)
