from django.urls import path

from . import views


app_name = "htmx"
urlpatterns = [
    path("", views.NotificationProfileListView.as_view(), name="notificationprofile-list"),
    path("profiles/create/", views.NotificationProfileCreateView.as_view(), name="notificationprofile-create"),
    path("profiles/<pk>/", views.NotificationProfileDetailView.as_view(), name="notificationprofile-detail"),
    path("profiles/<pk>/update/", views.NotificationProfileUpdateView.as_view(), name="notificationprofile-update"),
    path("profiles/<pk>/delete/", views.NotificationProfileDeleteView.as_view(), name="notificationprofile-delete"),
]
