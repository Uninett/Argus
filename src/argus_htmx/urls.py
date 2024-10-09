from django.urls import path, include
from django.contrib.auth import views as auth_views

from argus.auth.views import LogoutView

from .incidents.urls import urlpatterns as incident_urls
from .timeslots.urls import urlpatterns as timeslot_urls
from .notificationprofiles.urls import urlpatterns as notificationprofile_urls
from .destinations.urls import urlpatterns as destination_urls
from .themes.urls import urlpatterns as theme_urls
from .dateformat.urls import urlpatterns as dateformat_urls

app_name = "htmx"
urlpatterns = [
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    # path("accounts/", include("django.contrib.auth.urls")),
    path("incidents/", include(incident_urls)),
    path("timeslots/", include(timeslot_urls)),
    path("notificationprofiles/", include(notificationprofile_urls)),
    path("destinations/", include(destination_urls)),
    path("themes/", include(theme_urls)),
    path("dateformat/", include(dateformat_urls)),
]
