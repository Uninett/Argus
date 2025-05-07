from django.urls import include, path


urlpatterns = [
    path("oidc/", include("social_django.urls", namespace="social")),
]
