from django.urls import path, include

from . import views


app_name = "htmx"
urlpatterns = [
    path("", views.incident_list, name="incident-list"),
    path("<int:pk>/", views.incident_detail, name="incident-detail"),
    path("<int:pk>/ack/", views.incident_add_ack, name="incident-add-ack"),
]
