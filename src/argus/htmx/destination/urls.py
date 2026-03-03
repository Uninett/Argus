from django.urls import path

from .views import (
    DestinationListView,
    DestinationCreateView,
    DestinationUpdateView,
    DestinationDeleteView,
)

app_name = "htmx"
urlpatterns = [
    path("", DestinationListView.as_view(), name="destination-list"),
    path("create/", DestinationCreateView.as_view(), name="destination-create"),
    path("<int:pk>/update/", DestinationUpdateView.as_view(), name="destination-update"),
    path("<int:pk>/delete/", DestinationDeleteView.as_view(), name="destination-delete"),
]
