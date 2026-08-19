"""
How to use:

Append the "context_processors" list for the TEMPLATES-backend
``django.template.backends.django.DjangoTemplates`` with the full dotted path.

See django settings for ``TEMPLATES``.
"""

from packaging.version import InvalidVersion, Version

from argus.site.views import get_version
from argus.versioncheck.models import LastSeenVersion


def update_available(request):
    if not getattr(request.user, "is_staff", False):
        return {"update_available": False, "latest_seen_version": None}

    latest_seen_version = _get_latest_seen_version()
    is_newer = bool(latest_seen_version) and _is_newer(latest_seen_version, get_version())

    return {
        "update_available": is_newer,
        "latest_seen_version": latest_seen_version,
    }


def _get_latest_seen_version():
    # Compare by parsed version rather than by timestamp/insertion order, in
    # case a lower version was ever recorded after a higher one (e.g. a
    # stale/retried task).
    parsed = []
    for v in LastSeenVersion.objects.values_list("version", flat=True):
        try:
            parsed.append((Version(v).base_version, v))
        except InvalidVersion:
            continue
    if not parsed:
        return None
    return max(parsed, key=lambda pair: Version(pair[0]))[1]


def _is_newer(candidate_version, current_version):
    # Compare base versions on both sides so a dev/post/local build of an
    # already-released version (e.g. "2.8.0.post44+g58afd3be.d20260424")
    # doesn't falsely appear outdated relative to its own release ("2.8.0").
    try:
        candidate = Version(Version(candidate_version).base_version)
        current = Version(Version(current_version).base_version)
    except (InvalidVersion, TypeError):
        return False
    return candidate > current
