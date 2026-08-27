import logging
from typing import Any, Optional, Tuple
from urllib.parse import urljoin

import requests

from django.conf import settings
from django.db import transaction

from argus.versioncheck.models import PyPIVersion
from argus.site.views import get_version

LOG = logging.getLogger(__name__)


__all__ = [
    "VersionCheckError",
    "fetch_info_from_pypi",
    "fetch_latest_version_and_upload_time",
    "get_latest_registered_version",
    "register_and_return_latest_version",
    "register_version",
]


class VersionCheckError(Exception):
    pass


def fetch_info_from_pypi():
    """Fetch all info about argus-server that PyPI has"""
    # Custom user agent so we can see in logs if it's an argus instance
    # or just a crawler that's checking the page
    version = get_version()
    response = requests.get(
        urljoin(settings.PYPI_URL, "/pypi/argus-server/json"),
        timeout=5,
        headers={"User-Agent": f"Argus-server-{version}"},
    )
    try:
        response.raise_for_status()
    except requests.RequestException as e:
        LOG.error("Error fetching latest version: %s", e)
        raise VersionCheckError("Possible network problem") from e
    return response.json()


def fetch_latest_version_and_upload_time():
    """Fetch version and upload time of latest release from the web

    Chooses the most recent upload time, there's one per upload type.
    """
    pypidump = fetch_info_from_pypi()

    try:
        latest_version = _get_latest_version_from_pypi_dump(pypidump)
    except KeyError as e:
        msg = "Info from PyPI was malformed, no version"
        LOG.error(msg)
        raise VersionCheckError(msg) from e
    try:
        upload_time = _get_latest_upload_time_for_version_from_pypi_dump(pypidump, latest_version)
    except (KeyError, ValueError) as e:
        msg = "Info from PyPI was malformed, release-object broken"
        LOG.error(msg)
        raise VersionCheckError(msg) from e
    return latest_version, upload_time


def get_latest_registered_version(suppress_errors: bool = True) -> Optional[PyPIVersion]:
    """Fetch the latest known released version that argus has stored locally"""
    msg = "No versions have been fetched"
    try:
        return PyPIVersion.objects.latest("upload_time")
    except PyPIVersion.DoesNotExist as e:
        LOG.warning(msg)
        if suppress_errors:
            return None
        raise VersionCheckError(msg) from e


def register_and_return_latest_version(suppress_errors: bool = True) -> Tuple[Optional[PyPIVersion], bool]:
    """Attempt updating the internal store of version from the web

    Returns the latest stored version if it exists, updated or not
    Returns None on errors if suppress_errors is True, else
    raises a VersionCheckError with more information.
    """
    try:
        latest_version, upload_time = fetch_latest_version_and_upload_time()
    except VersionCheckError:
        if suppress_errors:
            return None, None
        return get_latest_registered_version(suppress_errors), False
    return register_version(latest_version, upload_time)


@transaction.atomic
def register_version(latest_version, upload_time) -> Tuple[PyPIVersion, bool]:
    """Save a new version"""
    qs = PyPIVersion.objects.select_for_update()
    return qs.get_or_create(version=latest_version, upload_time=upload_time)


# PyPI parsing helpers


def _get_latest_version_from_pypi_dump(pypidict):
    """Select latest released version number from PyPI dump"""
    return pypidict["info"]["version"]


def _get_latest_upload_time_for_version_from_pypi_dump(pypidict: dict[str, Any], versionstring: str):
    """Select upload times for latest released version from PyPI dump"""
    release_info = pypidict["releases"][versionstring]
    # release_info is a list of releases for that version, one per type
    upload_dates = [release["upload_time_iso_8601"] for release in release_info]
    return max(upload_dates)
