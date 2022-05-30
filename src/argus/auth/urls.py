from django.urls import path
from rest_framework import routers

from . import views


router = routers.SimpleRouter()


app_name = "auth"
urlpatterns = [
    # path("login/", django_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("refresh-token/", views.RefreshTokenView.as_view(), name="refresh-token"),
    path("user/", views.CurrentUserView.as_view(), name="current-user"),
    path("users/<int:pk>/", views.BasicUserDetail.as_view(), name="user"),
] + router.urls
