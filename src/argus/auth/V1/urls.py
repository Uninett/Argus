from django.urls import path
from rest_framework import routers

from . import views as views_V1
from .. import views


router = routers.SimpleRouter()


app_name = "auth"
urlpatterns = [
    # path("login/", django_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("phone-number/", views_V1.PhoneNumberViewV1.as_view(), name="phone-number"),
    path("user/", views_V1.CurrentUserViewV1.as_view(), name="current-user"),
    path("users/<int:pk>/", views.BasicUserDetail.as_view(), name="user"),
] + router.urls
