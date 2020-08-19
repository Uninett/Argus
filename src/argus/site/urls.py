"""Argus URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import include, path, re_path
from social_django.urls import extra

from argus.auth.views import ObtainNewAuthToken
from argus.dataporten import views as dataporten_views


api_urls = [
    path("auth/", include("argus.auth.urls")),
    path("incidents/", include("argus.incident.urls")),
    path("notificationprofiles/", include("argus.notificationprofile.urls")),
    path("token-auth/", ObtainNewAuthToken.as_view(), name="api-token-auth"),
]

psa_urls = [
    # Overrides social_django's `complete` view
    re_path(fr"^complete/(?P<backend>[^/]+){extra}$", dataporten_views.login_wrapper, name="complete"),
    path("", include("social_django.urls", namespace="social")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("oidc/", include(psa_urls)),
    path("api/v1/", include(api_urls)),
]
