from django.urls import path

from .views import destination_list, create_destination, delete_destination, update_destination

app_name = "destination"
urlpatterns = [
    path("", destination_list, name="destination-list"),
    path("<str:media>/create/", create_destination, name="destination-create"),
    path("<int:pk>/delete/", delete_destination, name="destination-delete"),
    path("<int:pk>-<str:media>/update/", update_destination, name="destination-update"),
]
