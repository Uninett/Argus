from django.urls import path

from . import views, filter


app_name = "htmx"
urlpatterns = [
    path("", views.incident_list, name="incident-list"),
    path("<int:pk>/", views.incident_detail, name="incident-detail"),
    path("update/<str:action>/", views.incident_update, name="incident-update"),
    path("filter/", views.filter_form, name="incident-filter"),
    path("filter-list/", filter.FilterListView.as_view(), name="filter-list"),
    path("select-filter/", views.filter_select, name="select-filter"),
    path("filter-create/", views.create_filter, name="filter-create"),
    path("filter/delete/<int:pk>/", views.delete_filter, name="filter-delete"),
    path("filter/update/<int:pk>/", views.update_filter, name="filter-update"),
    path("filter/existing/", views.get_existing_filters, name="existing-filters"),
]
