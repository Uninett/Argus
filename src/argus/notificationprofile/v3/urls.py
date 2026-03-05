from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r"media", views.MediaViewSet)
router.register(r"destinations", views.DestinationConfigViewSet)

app_name = "notification-profile"
urlpatterns = router.urls
