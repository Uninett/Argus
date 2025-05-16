from django.urls import include, path

from . import views

app_name = "auth"
urlpatterns = [
    path("user/", views.CurrentUserView.as_view(), name="current-user"),
    path("users/<int:pk>/", views.BasicUserDetail.as_view(), name="user"),
    path("", include("argus.auth.drftoken.urls")),
]
