from django.urls import path

from . import views

app_name = "notification-profile"
urlpatterns = [
    path("", views.NotificationProfileList.as_view(), name="notification-profiles"),
    path("<int:pk>/", views.NotificationProfileDetail.as_view(), name="notification-profile"),
    path(
        "<int:notification_profile_pk>/incidents/",
        views.incidents_filtered_by_notification_profile_view,
        name="notification-profile-incidents",
    ),
    path("timeslots/", views.TimeslotList.as_view(), name="timeslots"),
    path("timeslots/<int:pk>/", views.TimeslotDetail.as_view(), name="timeslot"),
    path("filters/", views.FilterList.as_view(), name="filters"),
    path("filters/<int:pk>/", views.FilterDetail.as_view(), name="filter"),
    path("filterpreview/", views.filter_preview_view, name="filter-preview"),
]
