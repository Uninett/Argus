from django.urls import path

from .views import destination_list, destination_delete

app_name = "htmx"
urlpatterns = [
    path("", destination_list, name="destination-list"),
    path("<int:pk>/delete/", destination_delete, name="destination-delete"),
]
