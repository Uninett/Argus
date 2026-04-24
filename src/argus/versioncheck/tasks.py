import logging
import requests
from urllib.parse import urljoin

from django_tasks import task
from django.conf import settings

from argus.versioncheck.models import LastSeenVersion
from argus.site.views import get_version

LOG = logging.getLogger(__name__)


@task
def task_register_latest_version():
    try:
        latest_version = get_latest_version()
        LastSeenVersion.objects.get_or_create(version=latest_version)
    except requests.RequestException as e:
        LOG.error("Error getting latest version: %s", e)


def get_latest_version():
    # Custom user agent so we can see in logs if it's an argus instance or just a crawler that's checking the page
    version = get_version()
    response = requests.get(
        urljoin(settings.PYPI_URL, "/pypi/argus-server/json"),
        timeout=5,
        headers={"User-Agent": f"Argus-server-{version}"},
    )
    response.raise_for_status()
    data = response.json()
    return data["info"]["version"]
