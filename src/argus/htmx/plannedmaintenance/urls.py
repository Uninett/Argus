from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("create/", views.PlannedMaintenanceCreateView.as_view(), name="plannedmaintenance-create"),
    path("<pk>/cancel/", views.PlannedMaintenanceCancelView.as_view(), name="plannedmaintenance-cancel"),
    path("<pk>/delete/", views.PlannedMaintenanceDeleteView.as_view(), name="plannedmaintenance-delete"),
    path("<pk>/update/", views.PlannedMaintenanceUpdateView.as_view(), name="plannedmaintenance-update"),
    path("", views.PlannedMaintenanceListView.as_view(), name="plannedmaintenance-list"),
    path("<pk>/", views.PlannedMaintenanceDetailView.as_view(), name="plannedmaintenance-detail"),
]
