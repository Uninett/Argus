"""Argus URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from functools import partial
from urllib.parse import urljoin

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from argus.constants import API_STABLE_VERSION, API_STABLE_SCHEMA_VIEWNAME
from argus.notificationprofile.v2.views import SchemaView
from argus.site.utils import get_urlpatterns, prefix_urlpatterns
from argus.site.views import about, index, MetadataView, api_gone, error, health_check

api_v1_gone = partial(api_gone, message="API v1 has been removed")

api_urls = [
    path(
        "api/schema/",
        SpectacularAPIView.as_view(api_version=API_STABLE_VERSION),
        name=API_STABLE_SCHEMA_VIEWNAME,
    ),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name=API_STABLE_SCHEMA_VIEWNAME),
        name=f"swagger-ui-{API_STABLE_VERSION}",
    ),
    re_path(r"^api/v1/.*$", api_v1_gone),
    path("api/v2/", include(("argus.site.api_v2_urls", "api"), namespace="v2")),
    path("api/v3/", include(("argus.site.api_v3_urls", "api"), namespace="v3")),
    # path('api/sessionauth/', include('rest_framework.urls', namespace='rest_framework')),
    path("api/", MetadataView.as_view(), name="metadata"),
    path("json-schema/<slug:slug>", SchemaView.as_view(), name="json-schema"),
    path("", index, name="api-home"),
]

frontend_urls = [
    path(".error/", error, name="error"),
    # named so that deployments serving Argus from a sub-path can reverse it
    path(".still-alive/", health_check, name="health-check"),
    path("about/", about, name="about"),
    path("about/", include("argus.versioncheck.urls")),
    path("admin/", admin.site.urls),
]


def build_favicon_urls() -> list:
    """The bare /favicon.ico a browser asks for when a page names no icon

    STATIC_URL follows the sub-path, so the target is joined rather than
    written out, and joined here rather than at module import so that it
    tracks the setting the same way the rest of the urlconf does.

    Not staticfiles_storage.url(): under the manifest storage used in
    production that raises at import until collectstatic has run, trading a
    wrong url for a dead site. Temporary rather than permanent, because the
    target moves whenever STATIC_URL or the sub-path does and a permanent
    redirect would stay pinned in browsers long after.
    """
    return [
        path(
            "favicon.ico",
            RedirectView.as_view(url=urljoin(settings.STATIC_URL, "favicon.svg"), permanent=False),
        ),
    ]


def build_urlpatterns(suburl: str) -> list:
    """Compose this site's urlconf below the sub-path ``suburl``

    Callable so that tests can build the urlconf under a prefix without
    reloading modules: django reads urlpatterns once, at import, so the
    module-level binding below cannot follow a later change to SITE_SUBURL.

    Everything goes inside the wrap, extra and overriding apps included. Those
    exist to extend or replace Argus's own urls, so an Argus that lives below a
    sub-path is where they belong too; leaving them outside would produce a
    site that half-follows the prefix, which fails silently rather than loudly.
    """
    return prefix_urlpatterns(
        get_urlpatterns(settings.OVERRIDING_APPS)
        + build_favicon_urls()
        + api_urls
        + frontend_urls
        + get_urlpatterns(settings.EXTRA_APPS),
        suburl,
    )


urlpatterns = build_urlpatterns(settings.SITE_SUBURL)
