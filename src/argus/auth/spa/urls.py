from django.urls import path

from . import views


app_name = "auth"
urlpatterns = [
    path("refresh-token/", views.RefreshTokenView.as_view(), name="refresh-token"),
]
