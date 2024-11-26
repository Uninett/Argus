from django.urls import include, path, re_path

from social_django.urls import extra

from argus.spa.views import AuthMethodListView, LogoutView


urlpatterns = [
    path("login-methods/", AuthMethodListView.as_view(), name="login-methods"),
    path("api/v1/auth/logout/", LogoutView.as_view(), name="v1-logout"),
    path("api/v2/auth/logout/", LogoutView.as_view(), name="v2-logout"),
]
