from django.urls import path, re_path

from . import views


app_name = "htmx"
urlpatterns = [
    path("create/", views.PlannedMaintenanceCreateView.as_view(), name="plannedmaintenance-create"),
    path("search-filters/", views.search_filters, name="search-filters"),
    re_path(r"^(?P<tab>upcoming|past)?/$", views.PlannedMaintenanceListView.as_view(), name="plannedmaintenance-list"),
    path("<pk>/cancel/", views.PlannedMaintenanceCancelView.as_view(), name="plannedmaintenance-cancel"),
    path("<pk>/delete/", views.PlannedMaintenanceDeleteView.as_view(), name="plannedmaintenance-delete"),
    path("<pk>/update/", views.PlannedMaintenanceUpdateView.as_view(), name="plannedmaintenance-update"),
    path("<pk>/", views.PlannedMaintenanceDetailView.as_view(), name="plannedmaintenance-detail"),
    path("", views.PlannedMaintenanceListView.as_view(), name="plannedmaintenance-list-upcoming"),
]
