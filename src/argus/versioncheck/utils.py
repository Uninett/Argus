from datetime import timedelta
import logging
import requests
from urllib.parse import urljoin

from django.conf import settings
from django.utils.timezone import now

from argus.versioncheck.models import LastSeenVersion
from argus.site.views import get_version

LOG = logging.getLogger(__name__)


__all__ = [
    "get_latest_version",
    "register_latest_version",
    "update_latest_version_on_access",
]


def get_latest_version():
    """Fetch version of latest release from the web"""
    # Custom user agent so we can see in logs if it's an argus instance
    # or just a crawler that's checking the page
    version = get_version()
    response = requests.get(
        urljoin(settings.PYPI_URL, "/pypi/argus-server/json"),
        timeout=5,
        headers={"User-Agent": f"Argus-server-{version}"},
    )
    response.raise_for_status()
    data = response.json()
    return data["info"]["version"]


def register_latest_version():
    try:
        latest_version = get_latest_version()
    except requests.RequestException as e:
        LOG.error("Error getting latest version: %s", e)
    else:
        LastSeenVersion.objects.get_or_create(version=latest_version)


def update_latest_version_on_access():
    latest_registered_version = LastSeenVersion.objects.last()
    if latest_registered_version is None or latest_registered_version.timestamp < (now() - timedelta(days=1)):
        register_latest_version()
        latest_registered_version = LastSeenVersion.objects.last()
    return latest_registered_version.version
