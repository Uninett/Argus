from django.conf import settings
from django.urls import include, path

from argus.site.utils import get_urlpatterns, prefix_urlpatterns

from argus.htmx.appconfig import APP_SETTINGS


def build_urlpatterns(suburl: str) -> list:
    """Compose the htmx frontend's urlconf below the sub-path ``suburl``

    See argus.site.urls.build_urlpatterns for why this is callable.
    """
    urlpatterns = get_urlpatterns(APP_SETTINGS)
    urlpatterns += [
        path("oidc/", include("social_django.urls", namespace="social")),
    ]
    return prefix_urlpatterns(urlpatterns, suburl)


urlpatterns = build_urlpatterns(settings.SITE_SUBURL)
