"""Routing when Argus is served from a sub-path of a domain

The urlconf is composed at import, so these tests point ROOT_URLCONF at
``tests.site.urlconf_subsite`` rather than overriding ``SITE_SUBURL`` alone.
``SITE_SUBURL`` and ``STATIC_URL`` are overridden alongside it because a test
that moves only one of the three passes for the wrong reason: with ROOT_URLCONF
alone, url names follow the prefix while the literal paths in ``PUBLIC_URLS`` do
not, quietly leaving the api non-public, and the favicon redirect points at a
static root the sub-site does not have.
"""

import unittest

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.urls.resolvers import URLPattern, URLResolver

from argus.auth.factories import PersonUserFactory
from argus.htmx import root_urls
from argus.site.utils import prefix_urlpatterns


# Defined above the tests it decorates, unlike the helper at the bottom of this
# module: python evaluates a class decorator when the class is created
subsite = override_settings(
    ROOT_URLCONF="tests.site.urlconf_subsite",
    SITE_SUBURL="argus/",
    STATIC_URL="/argus/static/",
)


class SubsiteUrlconfShapeTests(unittest.TestCase):
    def test_given_a_suburl_then_every_url_should_move_below_it_and_nowhere_else(self):
        root_paths = flatten_urlpatterns(root_urls.build_urlpatterns(""))
        prefixed_paths = flatten_urlpatterns(root_urls.build_urlpatterns("argus/"))
        self.assertEqual(prefixed_paths, [f"/argus{path}" for path in root_paths])

    def test_given_no_suburl_then_the_urlconf_should_be_the_one_the_site_serves(self):
        # pins the builder to the live module binding, so it cannot drift from
        # what the process actually serves at the domain root
        self.assertEqual(
            flatten_urlpatterns(root_urls.build_urlpatterns("")),
            flatten_urlpatterns(root_urls.urlpatterns),
        )

    def test_given_no_suburl_then_prefixing_should_hand_back_the_very_same_list(self):
        urlpatterns = [object()]
        self.assertIs(prefix_urlpatterns(urlpatterns, ""), urlpatterns)


@subsite
class SubsiteReverseTests(SimpleTestCase):
    def test_given_a_sub_path_then_reversing_should_include_it(self):
        expected = {
            "htmx:incident-list": "/argus/incidents/",
            "htmx:login": "/argus/accounts/login/",
            "admin:index": "/argus/admin/",
            "health-check": "/argus/.still-alive/",
            "v2:openapi:schema": "/argus/api/v2/schema/",
        }
        for name, path in expected.items():
            with self.subTest(name=name):
                self.assertEqual(reverse(name), path)

    def test_given_a_sub_path_then_the_social_auth_include_should_move_with_it(self):
        # the namespaced include is the part that could be left behind, and
        # social_django builds its redirect uri by reversing this
        self.assertEqual(reverse("social:complete", args=("oidc",)), "/argus/oidc/complete/oidc/")
        self.assertEqual(reverse("social:begin", args=("oidc",)), "/argus/oidc/login/oidc/")


@subsite
class SubsiteRequestTests(TestCase):
    def test_given_a_sub_path_then_the_health_check_should_answer_below_it(self):
        response = self.client.get("/argus/.still-alive/")
        self.assertEqual(response.status_code, 204)

    def test_given_a_sub_path_then_an_unauthenticated_request_should_redirect_into_it(self):
        response = self.client.get("/argus/incidents/")
        self.assertRedirects(
            response,
            "/argus/accounts/login/?next=/argus/incidents/",
            fetch_redirect_response=False,
        )

    def test_given_a_sub_path_then_an_authenticated_request_should_reach_the_view(self):
        self.client.force_login(PersonUserFactory())
        response = self.client.get("/argus/incidents/")
        self.assertEqual(response.status_code, 200)

    def test_given_a_sub_path_then_the_favicon_should_redirect_inside_it(self):
        # the redirect target comes from STATIC_URL rather than the urlconf,
        # so it is the one route that could point back out of the sub-site.
        # Logged in because favicon.ico is not public, at the domain root
        # either, so an anonymous request only ever sees the login redirect
        self.client.force_login(PersonUserFactory())
        response = self.client.get("/argus/favicon.ico")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/argus/static/favicon.svg")

    def test_given_a_sub_path_then_the_root_paths_should_no_longer_resolve(self):
        for path in ("/incidents/", "/.still-alive/", "/admin/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)


def flatten_urlpatterns(urlpatterns, base="/"):
    """Yield every concrete url path in a urlconf, resolvers expanded"""
    paths = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            paths.extend(flatten_urlpatterns(pattern.url_patterns, base + str(pattern.pattern)))
        elif isinstance(pattern, URLPattern):
            paths.append(base + str(pattern.pattern))
    return paths
