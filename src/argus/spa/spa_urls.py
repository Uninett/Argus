from django.urls import include, path, re_path

from social_django.urls import extra

from argus.spa.views import AuthMethodListView, login_wrapper, LogoutView


urlpatterns = [
    path("login-methods/", AuthMethodListView.as_view(), name="login-methods"),
    # Overrides social_django's `complete` view
    re_path(rf"^oidc/complete/(?P<backend>[^/]+){extra}$", login_wrapper, name="complete"),
    path("oidc/", include("social_django.urls", namespace="social")),
    path("api/v1/logout", LogoutView.as_view(), name="v1-logout"),
    path("api/v2/logout", LogoutView.as_view(), name="v2-logout"),
]
