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

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from argus.notificationprofile.views import SchemaView
from argus.site.utils import get_urlpatterns
from argus.site.views import index, MetadataView, api_gone

api_v1_gone = partial(api_gone, message="API v1 has been removed")


urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.svg", permanent=True)),
    # path(".error/", error),  # Only needed when testing error pages and error behavior
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(api_version="v2"), name="schema-v2"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema-v2"), name="swagger-ui-v2"),
    re_path(r"^api/v1/.*$", api_v1_gone),
    path("api/v2/", include(("argus.site.api_v2_urls", "api"), namespace="v2")),
    # path('api/sessionauth/', include('rest_framework.urls', namespace='rest_framework')),
    path("api/", MetadataView.as_view(), name="metadata"),
    path("json-schema/<slug:slug>", SchemaView.as_view(), name="json-schema"),
    path("", index, name="api-home"),
]

# Extra/overriding apps

prefixed_urlpatterns = get_urlpatterns(settings.OVERRIDING_APPS)
if prefixed_urlpatterns:
    urlpatterns = prefixed_urlpatterns + urlpatterns

postfixed_urlpatterns = get_urlpatterns(settings.EXTRA_APPS)
if postfixed_urlpatterns:
    urlpatterns += postfixed_urlpatterns
