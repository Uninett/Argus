from django.urls import path

from . import views


urlpatterns = [
    path("refresh-token/", views.RefreshTokenView.as_view(), name="refresh-token"),
]
