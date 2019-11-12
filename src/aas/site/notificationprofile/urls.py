from django.urls import path

from . import views

app_name = "notificationprofile"
urlpatterns = [
    path("", views.NotificationProfileList.as_view()),
    path("<int:pk>", views.NotificationProfileDetail.as_view()),
    path("<int:notification_profile_pk>/alerts/", views.alerts_filtered_by_notification_profile_view),

    path("timeslotgroups/", views.TimeSlotGroupList.as_view()),
    path("timeslotgroups/<int:pk>", views.TimeSlotGroupDetail.as_view()),

    path("filters/", views.FilterList.as_view()),
    path("filters/<int:pk>", views.FilterDetail.as_view()),
]
