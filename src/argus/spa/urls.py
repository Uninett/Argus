from django.urls import include, path, re_path

from social_django.urls import extra

from argus.spa.dataporten.views import login_wrapper
from argus.spa.views import AuthMethodListView

from argus.site.urls import urlpatterns

spa_urlpatterns = [
    path("login-methods/", AuthMethodListView.as_view(), name="login-methods"),
    # Overrides social_django's `complete` view
    re_path(rf"^oidc/complete/(?P<backend>[^/]+){extra}$", login_wrapper, name="+++complete"),
    path("oidc/", include("social_django.urls", namespace="social")),
]


urlpatterns += spa_urlpatterns
