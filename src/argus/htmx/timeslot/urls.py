from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("", views.TimeslotListView.as_view(), name="timeslot-list"),
    path("create/", views.TimeslotCreateView.as_view(), name="timeslot-create"),
    path("<pk>/", views.TimeslotDetailView.as_view(), name="timeslot-detail"),
    path("<pk>/update/", views.TimeslotUpdateView.as_view(), name="timeslot-update"),
    path("<pk>/delete/", views.TimeslotDeleteView.as_view(), name="timeslot-delete"),
]
