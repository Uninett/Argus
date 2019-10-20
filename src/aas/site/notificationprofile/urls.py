from django.urls import path

from . import views

app_name = "notificationprofile"
urlpatterns = [
    path("", views.NotificationProfileView.as_view()),
    path("<int:profile_id>", views.NotificationProfileView.as_view()),
    path("alerts/", views.notification_profile_alerts_view),
]
