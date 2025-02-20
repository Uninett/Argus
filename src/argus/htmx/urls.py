from django.contrib.auth import views as django_auth_views
from django.urls import path, include

from .auth import views as auth_views
from .incident.urls import urlpatterns as incident_urls
from .timeslot.urls import urlpatterns as timeslot_urls
from .notificationprofile.urls import urlpatterns as notificationprofile_urls
from .destination.urls import urlpatterns as destination_urls
from .user.urls import urlpatterns as user_urls
from .views import IncidentListRedirectView

app_name = "htmx"
urlpatterns = [
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", django_auth_views.LogoutView.as_view(), name="logout"),
    # path("accounts/", include("django.contrib.auth.urls")),
    path("incidents/", include(incident_urls)),
    path("timeslots/", include(timeslot_urls)),
    path("notificationprofiles/", include(notificationprofile_urls)),
    path("destinations/", include(destination_urls)),
    path("user/", include(user_urls)),
    path("", IncidentListRedirectView.as_view(), name="root"),
]
