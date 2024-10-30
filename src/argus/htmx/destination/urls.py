from django.urls import path

from .views import destination_list

app_name = "htmx"
urlpatterns = [
    path("", destination_list, name="destination-list"),
]
