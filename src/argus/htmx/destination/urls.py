from django.urls import path

from .views import destination_list, create_htmx, delete_htmx, update_htmx

app_name = "htmx"
urlpatterns = [
    path("", destination_list, name="destination-list"),
    path("htmx-create/", create_htmx, name="htmx-create"),
    path("<int:pk>/htmx-delete/", delete_htmx, name="htmx-delete"),
    path("<int:pk>/htmx-update/", update_htmx, name="htmx-update"),
]
