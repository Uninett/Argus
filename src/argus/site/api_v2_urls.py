from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from argus.auth.views import ObtainNewAuthToken

openapi_urls = [
    path("", SpectacularAPIView.as_view(api_version="v2"), name="schema"),
    path("swagger-ui/", SpectacularSwaggerView.as_view(url_name="v2:openapi:schema"), name="swagger-ui"),
]

tokenauth_urls = [
    path("", ObtainNewAuthToken.as_view(), name="api-token-auth"),
]

urlpatterns = [
    path("schema/", include((openapi_urls, "openapi"))),
    path("auth/", include("argus.auth.urls")),
    path("incidents/", include("argus.incident.urls")),
    path("notificationprofiles/", include("argus.notificationprofile.urls")),
    path("token-auth/", include((tokenauth_urls, "auth"))),
]
