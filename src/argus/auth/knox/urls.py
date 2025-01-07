from django.urls import path

from . import views


urlpatterns = [
    path("login/", views.LoginView.as_view(), name="knox_login"),
    path("logout/", views.LogoutView.as_view(), name="knox_logout"),
    path("logoutall", views.LogoutAllView.as_view(), name="knox_logoutall"),
]
