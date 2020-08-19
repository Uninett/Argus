from django.contrib.auth import views as django_views
from django.urls import include, path
from rest_framework import routers

from . import views


router = routers.SimpleRouter()
router.register("phone-number", views.PhoneNumberViewSet)


app_name = "auth"
urlpatterns = [
    path("login/", django_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", django_views.LogoutView.as_view(), name="logout"),
    path("user/", views.CurrentUserView.as_view(), name="current-user"),
    path("", include(router.urls)),
]
