from django.urls import path, include

from . import views


app_name = "htmx"
urlpatterns = [
    path("", views.incidents, name="incidents"),
    path("<int:pk>/", views.incident_detail, name="incident-detail"),
    path("<int:pk>/ack/", views.incident_add_ack, name="incident-add-ack"),
    path("table/", views.incidents_table, name="incidents-table"),
]
