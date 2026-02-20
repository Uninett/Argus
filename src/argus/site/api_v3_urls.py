from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


openapi_urls = [
    path("", SpectacularAPIView.as_view(api_version="v3"), name="schema"),
    path("swagger-ui/", SpectacularSwaggerView.as_view(url_name="v3:openapi:schema"), name="swagger-ui"),
]

urlpatterns = [
    path("schema/", include((openapi_urls, "openapi"))),
    path("notificationprofiles/", include("argus.notificationprofile.v3.urls")),
]
