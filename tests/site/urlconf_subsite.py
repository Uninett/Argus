"""The real root urlconf, re-derived below a fixed sub-path

Imported by ``override_settings(ROOT_URLCONF=...)`` in the routing tests.
Django reads ``urlpatterns`` once, at import, so overriding ``SITE_SUBURL``
alone moves nothing; pointing the root urlconf here is what moves routing.

This module defines no urls of its own, so it cannot drift from the site it
is meant to protect.
"""

from argus.htmx.root_urls import build_urlpatterns


SUBURL = "argus/"

urlpatterns = build_urlpatterns(SUBURL)
