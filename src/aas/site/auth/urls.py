from django.contrib.auth import views as django_views
from django.urls import path

from . import views

app_name = "auth"
urlpatterns = [
    path(
        "login/",
        django_views.LoginView.as_view(
            template_name="auth/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path("logout/", django_views.LogoutView.as_view(), name="logout"),
    path("user/", views.get_user, name="user"),
]
