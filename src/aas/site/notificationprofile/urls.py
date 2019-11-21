from django.urls import path

from . import views

app_name = "notificationprofile"
urlpatterns = [
    path("", views.NotificationProfileList.as_view()),
    path("<int:pk>", views.NotificationProfileDetail.as_view()),
    path(
        "<int:notification_profile_pk>/alerts/",
        views.alerts_filtered_by_notification_profile_view,
    ),
    path("timeslots/", views.TimeSlotList.as_view()),
    path("timeslots/<int:pk>", views.TimeSlotDetail.as_view()),
    path("filters/", views.FilterList.as_view()),
    path("filters/<int:pk>", views.FilterDetail.as_view()),
    path("filterpreview/", views.filter_preview_view),
]
