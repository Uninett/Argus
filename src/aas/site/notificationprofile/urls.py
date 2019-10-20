from django.urls import path

from . import views

app_name = "notificationprofile"
urlpatterns = [
    path("", views.NotificationProfileList.as_view()),
    path("<int:pk>", views.NotificationProfileDetail.as_view()),
    path("alerts/", views.notification_profile_alerts_view),
]
