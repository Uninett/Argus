from django.urls import path

from . import views

app_name = "notificationprofile"
urlpatterns = [
    path("notification_profile/<username>", views.notification_profile_view, name="notification_profile"),
    path("create_notification_profile/", views.create_notification_profile_view, name="create_notification_profile"),
    path("delete_notification_profile/", views.delete_notification_profile_view, name="delete_notification_profile"),
    path("get_notification_profile/<username>", views.get_notification_profile_view, name="get_notification_profile"),
]
