from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register(r"", views.PlannedMaintenanceTaskViewSet)

app_name = "plannedmaintenance"
urlpatterns = router.urls
