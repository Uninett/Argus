from django.urls import path, include

app_name = "htmx"
urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
]
