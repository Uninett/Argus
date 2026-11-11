from django.conf import settings

from argus.site import urls as site_urls

from . import htmx_urls


def build_urlpatterns(suburl: str) -> list:
    """Compose the full urlconf, frontend and site both, below ``suburl``

    Each half is wrapped on its own rather than wrapping the concatenation, so
    that argus.site.urls stays correct as a root urlconf in its own right for
    deployments that serve only the API.
    """
    return htmx_urls.build_urlpatterns(suburl) + site_urls.build_urlpatterns(suburl)


urlpatterns = build_urlpatterns(settings.SITE_SUBURL)
