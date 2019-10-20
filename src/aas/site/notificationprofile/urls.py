from django.urls import path

from . import views

app_name = "notificationprofile"
urlpatterns = [
    path("alerts/", views.notification_profile_alerts_view, name="notification_profile_alerts"),
    path("create/", views.create_notification_profile_view, name="create_notification_profile"),
    path("delete/<int:profile_id>", views.delete_notification_profile_view, name="delete_notification_profile"),
    path("all/", views.get_notification_profiles_view, name="get_notification_profiles"),
]
