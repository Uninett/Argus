from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("incidents/", views.incidents, name="htmx_incidents"),
]
