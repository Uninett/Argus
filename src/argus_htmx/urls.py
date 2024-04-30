from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("incidents/", views.incidents, name="htmx_incidents"),
    path("incidents/<int:pk>/", views.incident_detail, name="htmx_incident_detail"),
    path("incidents/<int:pk>/ack/", views.incident_add_ack, name="htmx-incident-add-ack"),
]
