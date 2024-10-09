from argus.site.urls import urlpatterns

from .htmx_urls import urlpatterns as htmx_urlpatterns

urlpatterns = htmx_urlpatterns + urlpatterns
