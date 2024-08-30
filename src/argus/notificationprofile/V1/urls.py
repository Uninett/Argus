from django.urls import path
from rest_framework import routers

from .. import views
from . import views as views_V1

router = routers.SimpleRouter()
router.register(r"timeslots", views.TimeslotViewSet)
router.register(r"filters", views_V1.FilterViewSetV1)
router.register(r"", views_V1.NotificationProfileViewSetV1)

app_name = "notification-profile"
urlpatterns = [
    path("filterpreview/", views.filter_preview_view, name="filter-preview"),
] + router.urls
