from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_spectacular.utils import extend_schema, extend_schema_view

from argus.auth.drftoken.views import ObtainNewAuthToken


@extend_schema_view(
    get=extend_schema(deprecated=True),
)
class SpectacularAPIViewV1(SpectacularAPIView):
    pass


openapi_urls = [
    path("", SpectacularAPIViewV1.as_view(api_version="v1"), name="schema-v1"),
    path("swagger-ui/", SpectacularSwaggerView.as_view(url_name="v1:openapi:schema-v1"), name="swagger-ui-v1"),
]

tokenauth_urls = [
    path("", ObtainNewAuthToken.as_view(), name="api-token-auth"),
]

urlpatterns = [
    path("schema/", include((openapi_urls, "openapi"))),
    path("auth/", include("argus.auth.V1.urls")),
    path("incidents/", include("argus.incident.V1.urls")),
    path("notificationprofiles/", include("argus.notificationprofile.V1.urls")),
    path("token-auth/", include(tokenauth_urls)),
]
