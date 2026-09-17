from django.conf import settings
from django.urls import include, path

from argus.site.utils import get_urlpatterns

from argus.htmx.appconfig import APP_SETTINGS

urlpatterns = get_urlpatterns(APP_SETTINGS)
urlpatterns += [
    path("oidc/", include("social_django.urls", namespace="social")),
]

if settings.SITE_SUBURL:
    urlpatterns = [path(settings.SITE_SUBURL, include(urlpatterns))]
