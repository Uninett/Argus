from django.contrib import admin
from django.urls import include, path

from argus.spa.spa_urls import urlpatterns as spa_urlpatterns


urlpatterns = spa_urlpatterns + [
    path("admin/", admin.site.urls),
    path("api/v1/", include(("argus.site.api_v1_urls", "api"), namespace="v1")),
]
