from django.urls import path, include

from allauth.urls import urlpatterns as allauth_urlpatterns

from argus.auth.allauth.views import ArgusMFAAuthenticateView


mfa_urlpatterns = [path("authenticate/", ArgusMFAAuthenticateView.as_view(), name="mfa_authenticate")]


urlpatterns = [
    path(
        "accounts/",
        include(
            [
                path("2fa/", include(mfa_urlpatterns)),
                path("", include(allauth_urlpatterns)),
            ]
        ),
    ),
]
