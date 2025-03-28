from django.urls import path
from rest_framework import routers

from . import views as views


router = routers.SimpleRouter()
router.register(r"phone-number", views.PhoneNumberViewV1, basename="phone_number")


app_name = "auth"
urlpatterns = [
    # path("login/", django_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("user/", views.CurrentUserViewV1.as_view(), name="current-user"),
    path("users/<int:pk>/", views.BasicUserDetailV1.as_view(), name="user"),
] + router.urls
