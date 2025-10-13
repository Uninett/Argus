from django.urls import path, include

from .incident.urls import urlpatterns as incident_urls
from .timeslot.urls import urlpatterns as timeslot_urls
from .notificationprofile.urls import urlpatterns as notificationprofile_urls
from .destination.urls import urlpatterns as destination_urls
from .user.urls import urlpatterns as user_urls
from .views import IncidentListRedirectView, StyleGuideView


app_name = "htmx"
urlpatterns = [
    path("styleguide/", StyleGuideView.as_view(), name="styleguide"),
    path("incidents/", include(incident_urls)),
    path("timeslots/", include(timeslot_urls)),
    path("notificationprofiles/", include(notificationprofile_urls)),
    path("destinations/", include(destination_urls)),
    path("user/", include(user_urls)),
    path("", IncidentListRedirectView.as_view(), name="root"),
]
