from django.urls import path

from . import views


app_name = "auth"
urlpatterns = [
    path("user/", views.CurrentUserView.as_view(), name="current-user"),
    path("users/<int:pk>/", views.BasicUserDetail.as_view(), name="user"),
]
