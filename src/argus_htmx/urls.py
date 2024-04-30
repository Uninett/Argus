from django.urls import path, include
from django.contrib.auth import views as auth_views

from argus.auth.utils import get_psa_authentication_names
from argus.auth.views import LogoutView

from . import views


app_name = "htmx"
urlpatterns = [
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(extra_context={"oauth2_backends": get_psa_authentication_names()}),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    #path("accounts/", include("django.contrib.auth.urls")),
    path("incidents/", views.incidents, name="htmx_incidents"),
    path("incidents/<int:pk>/", views.incident_detail, name="htmx_incident_detail"),
    path("incidents/<int:pk>/ack/", views.incident_add_ack, name="htmx-incident-add-ack"),
]
