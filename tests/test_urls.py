from unittest import TestCase

from django.conf import settings
from django.core.exceptions import ViewDoesNotExist
from django.urls.resolvers import get_resolver, URLPattern, URLResolver


# Only paths/views created by us. Autogenerated stuff in the admin not needed
# Get entries for the list via ``manage.py show_urls``
NECESSARY_PATHS = {
    "/api/schema/",
    "/api/schema/swagger-ui/",
    "/api/v1/auth/logout/",
    "/api/v1/auth/phone-number/",
    "/api/v1/auth/phone-number/<pk>/",
    "/api/v1/auth/user/",
    "/api/v1/auth/users/<int:pk>/",
    "/api/v1/incidents/",
    "/api/v1/incidents/<int:incident_pk>/acks/",
    "/api/v1/incidents/<int:incident_pk>/acks/<int:pk>/",
    "/api/v1/incidents/<int:incident_pk>/events/",
    "/api/v1/incidents/<int:incident_pk>/events/<int:pk>/",
    "/api/v1/incidents/<pk>/",
    "/api/v1/incidents/<pk>/ticket_url/",
    "/api/v1/incidents/metadata/",
    "/api/v1/incidents/mine/",
    "/api/v1/incidents/open+unacked/",
    "/api/v1/incidents/open/",
    "/api/v1/incidents/source-types/",
    "/api/v1/incidents/source-types/<pk>/",
    "/api/v1/incidents/sources/",
    "/api/v1/incidents/sources/<pk>/",
    "/api/v1/notificationprofiles/",
    "/api/v1/notificationprofiles/<pk>/",
    "/api/v1/notificationprofiles/<pk>/incidents/",
    "/api/v1/notificationprofiles/filterpreview/",
    "/api/v1/notificationprofiles/filters/",
    "/api/v1/notificationprofiles/filters/<pk>/",
    "/api/v1/notificationprofiles/preview/",
    "/api/v1/notificationprofiles/timeslots/",
    "/api/v1/notificationprofiles/timeslots/<pk>/",
    "/api/v1/token-auth/",
}


class UrlpatternFlattener:
    def __init__(self, urlpatterns=None, base="", namespace=None):
        if urlpatterns is None:
            urlconf = __import__(settings.ROOT_URLCONF, {}, {}, [""])
            urlpatterns = urlconf.urlpatterns
            base = "/"
        self.urlpatterns = urlpatterns
        self.base = base
        self.namespace = namespace
        self.flat_urlpatterns = self.extract_views_from_urlpatterns(urlpatterns, base, namespace)

    @property
    def paths(self):
        paths = []
        for _, path, _ in self.flat_urlpatterns:
            paths.append(path)
        return paths

    def extract_views_from_urlpatterns(self, urlpatterns, base="", namespace=None):
        """
        Return a list of views from a list of urlpatterns.

        Each object in the returned list is a three-tuple: (view_func, regex, name)
        """
        views = []
        for p in urlpatterns:
            if isinstance(p, URLPattern):
                try:
                    if not p.name:
                        name = p.name
                    elif namespace:
                        name = "{0}:{1}".format(namespace, p.name)
                    else:
                        name = p.name
                    pattern = str(p.pattern)
                    views.append((p.callback, base + pattern, name))
                except ViewDoesNotExist:
                    continue
            elif isinstance(p, URLResolver):
                try:
                    patterns = p.url_patterns
                except ImportError:
                    continue
                if namespace and p.namespace:
                    _namespace = "{0}:{1}".format(namespace, p.namespace)
                else:
                    _namespace = p.namespace or namespace
                pattern = str(p.pattern)
                views.extend(self.extract_views_from_urlpatterns(patterns, base + pattern, namespace=_namespace))
            elif hasattr(p, "_get_callback"):
                try:
                    views.append((p._get_callback(), base + str(p.pattern), p.name))
                except ViewDoesNotExist:
                    continue
            elif hasattr(p, "url_patterns") or hasattr(p, "_get_url_patterns"):
                try:
                    patterns = p.url_patterns
                except ImportError:
                    continue
                views.extend(self.extract_views_from_urlpatterns(patterns, base + str(p.pattern), namespace=namespace))
            else:
                raise TypeError("%s does not appear to be a urlpattern object" % p)
        return views


class UrlsTest(TestCase):
    def test_no_necessary_paths_should_be_missing(self):
        installed_paths = set(UrlpatternFlattener().paths)
        missing = NECESSARY_PATHS - installed_paths
        self.assertEqual(missing, set())