from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("", views.NotificationProfileListView.as_view(), name="notificationprofile-list"),
    path("create/", views.NotificationProfileCreateView.as_view(), name="notificationprofile-create"),
    path("field/filters/", views.filters_form_view, name="notificationprofile-filters-field-create"),
    path("field/destinations/", views.destinations_form_view, name="notificationprofile-destinations-field-create"),
    path("<pk>/", views.NotificationProfileDetailView.as_view(), name="notificationprofile-detail"),
    path("<pk>/update/", views.NotificationProfileUpdateView.as_view(), name="notificationprofile-update"),
    path("<pk>/delete/", views.NotificationProfileDeleteView.as_view(), name="notificationprofile-delete"),
    path("<pk>/field/filters/", views.filters_form_view, name="notificationprofile-filters-field-update"),
    path(
        "<pk>/field/destinations/", views.destinations_form_view, name="notificationprofile-destinations-field-update"
    ),
]
