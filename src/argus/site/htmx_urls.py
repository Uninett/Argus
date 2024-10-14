"""Argus URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

from django.conf import settings
from django.urls import include, path, re_path


from argus.site.utils import get_urlpatterns
from argus.site.views import index

from .urls import urlpatterns

# Frontend

_FRONTEND_APPS = getattr(settings, "FRONTEND_APPS", False)
if _FRONTEND_APPS:
    # fancy frontend
    psa_urls = [
        path("", include("social_django.urls", namespace="social")),
    ]
    frontend_urlpatterns = get_urlpatterns(_FRONTEND_APPS)
    urlpatterns = (
        frontend_urlpatterns
        + urlpatterns
        + [
            path("oidc/", include(psa_urls)),
        ]
    )
else:
    # minimalistic frontend, maybe SPA somewhere else
    from social_django.urls import extra

    from argus.dataporten.views import login_wrapper

    psa_urls = [
        # Overrides social_django's `complete` view
        re_path(
            rf"^complete/(?P<backend>[^/]+){extra}$",
            login_wrapper,
            name="complete",
        ),
        path("", include("social_django.urls", namespace="social")),
    ]
    urlpatterns += [
        path("oidc/", include(psa_urls)),
        path("", index, name="api-home"),
    ]
