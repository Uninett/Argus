from django.contrib.auth import views as django_auth_views
from django.urls import include, path

from argus.auth.psa.htmx.views import PSALoginView


urlpatterns = [
    path("accounts/login/", PSALoginView.as_view(), name="login"),
    path("accounts/logout/", django_auth_views.LogoutView.as_view(), name="logout"),
    path("oidc/", include("social_django.urls", namespace="social")),
]
