from django.urls import re_path

from social_django.urls import extra

from argus.spa.views import login_wrapper
from argus.spa.urls import urlpatterns as spa_urlpatterns
from argus.auth.psa.urls import urlpatterns as psa_urlpatterns


urlpatterns = (
    spa_urlpatterns
    + [
        # Overrides social_django's `complete` view
        re_path(rf"^oidc/complete/(?P<backend>[^/]+){extra}$", login_wrapper, name="complete")
    ]
    + psa_urlpatterns
)
