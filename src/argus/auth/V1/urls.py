from django.urls import path
from rest_framework import routers

from . import views as views_V1
from .. import views


router = routers.SimpleRouter()
router.register(r"phone-number", views_V1.PhoneNumberViewV1, basename="phone_number")


app_name = "auth"
urlpatterns = [
    # path("login/", django_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("user/", views_V1.CurrentUserViewV1.as_view(), name="current-user"),
    path("users/<int:pk>/", views.BasicUserDetail.as_view(), name="user"),
] + router.urls
