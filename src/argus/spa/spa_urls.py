from django.urls import include, path, re_path

from social_django.urls import extra

from argus.spa.views import login_wrapper
from argus.spa.urls import urlpatterns as spa_urlpatterns


urlpatterns = spa_urlpatterns + [
    # Overrides social_django's `complete` view
    re_path(rf"^oidc/complete/(?P<backend>[^/]+){extra}$", login_wrapper, name="complete"),
    path("oidc/", include("social_django.urls", namespace="social")),
]
