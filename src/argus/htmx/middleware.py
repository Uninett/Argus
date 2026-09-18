import logging

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import resolve_url
from django.template import loader
from django.urls import NoReverseMatch
from django.utils.deprecation import MiddlewareMixin
from django_htmx.http import HttpResponseClientRedirect
from django.contrib import messages

from argus.site.settings import prefix_relative_url
from .request import HtmxHttpRequest

LOG = logging.getLogger(__name__)


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, _view_args, _view_kwargs):
        assert hasattr(request, "user"), (
            "The LoginRequiredMiddleware requires authentication middleware "
            "to be installed. Edit your MIDDLEWARE%s setting to insert "
            "'django.contrib.auth.middleware.AuthenticationMiddleware' "
            "before this middleware." % ("_CLASSES" if settings.MIDDLEWARE is None else "")
        )

        # If path is public, allow
        for url in self.public_urls:
            if request.path.startswith(url):
                return None

        # If CBV has the attribute login_required == False, allow
        view_class = getattr(view_func, "view_class", None)
        if view_class and not getattr(view_class, "login_required", True):
            return None

        # If view_func.login_required == False, allow
        if not getattr(view_func, "login_required", True):
            return None

        # Allow authenticated users
        if request.user.is_authenticated:
            return None

        # Redirect unauthenticated users to login page
        response = redirect_to_login(request.get_full_path(), redirect_field_name="next")
        if getattr(request, "htmx", False):
            response = HttpResponseClientRedirect(response.url)

        return response

    @property
    def public_urls(self) -> tuple[str, ...]:
        """Paths that may be visited without logging in, as seen from outside

        Rebuilt on every access, deliberately. Do not move this back into
        __init__, and do not turn it into a cached_property: django builds the
        middleware chain once per process, before the first request, so
        anything computed or cached there stays frozen for the life of the
        process.

        Frozen is wrong here for two reasons. This value is derived from
        PUBLIC_URLS, SITE_SUBURL and the urlconf, and a test that overrides any
        of them against a frozen copy sees the stale value, passes, and asserts
        nothing; the tests that exercise Argus under a url sub-path are exactly
        that shape. Resolving during chain construction also requires a urlconf
        that is already loaded, which is not guaranteed that early.

        Rebuilding costs tens of microseconds for the three entries Argus
        ships, against a request measured in milliseconds. That is the whole
        price, and it buys correctness under every ordering.

        An entry that cannot be resolved is skipped rather than raised.
        Resolution happens per request, so raising would take down every url
        on every request, including the ones this list exists to open up. That
        makes the logged warning the only signal a misconfigured entry gives,
        which a startup check would improve on.
        """
        urls = getattr(settings, "PUBLIC_URLS", ())
        suburl = getattr(settings, "SITE_SUBURL", "")

        public_urls = []
        for url in urls:
            try:
                resolved = resolve_url(url)
            except NoReverseMatch:
                _warn_once_about_unresolvable(url)
                continue
            public_urls.append(prefix_relative_url(resolved, suburl))
        return tuple(public_urls)


def _warn_once_about_unresolvable(url: str) -> None:
    """Complain about a PUBLIC_URLS entry, but only the first time

    Public urls are resolved per request, so an entry that stays unresolvable
    would otherwise log once per request for the life of the process, which is
    how an access log fills a disk. The set is bounded by the number of
    distinct bad entries, which is a handful at worst.
    """
    if url in _UNRESOLVABLE_PUBLIC_URLS:
        return
    _UNRESOLVABLE_PUBLIC_URLS.add(url)
    LOG.warning("Ignoring PUBLIC_URLS entry that this site cannot resolve: %r", url)


_UNRESOLVABLE_PUBLIC_URLS = set()


class HtmxMessageMiddleware(MiddlewareMixin):
    """
    For htmx requests, adds messages to the #notification-messages div defined in
    `templates/messages/_notification_messages.html` using htmx's hx-swap-oob feature
    """

    TEMPLATE = "messages/_notification_messages_htmx_append.html"

    def process_exception(self, request, exception):
        error_msg = f"{type(exception).__name__}: {exception}" if str(exception) else type(exception).__name__
        messages.error(request, error_msg)
        LOG.exception("HTMX request failed: %s", error_msg)
        return None

    def process_response(self, request: HtmxHttpRequest, response: HttpResponse) -> HttpResponse:
        if not request.htmx:
            return response

        # Ignore redirections because HTMX cannot read the headers
        if 300 <= response.status_code < 400:
            return response

        # do not add messages to hx redirects/refreshes
        if response.headers.get("HX-Refresh") == "true" or {"HX-Redirect", "HX-Location"} & response.headers.keys():
            return response

        if not response.writable():
            return response

        # For HTMX error responses, the view should make sure to write the appropriate message to
        # django messages framework. However, if it doesn't, we add a (generic) message so that we
        # can at least send some indication to the user that something has gone wrong.
        if response.status_code >= 400:
            storage = messages.get_messages(request)
            has_error_message = any("error" in message.tags for message in storage)
            storage.used = False
            if not has_error_message:
                error_msg = f"{response.status_code}: {response.reason_phrase}"
                LOG.error("HTMX request returned %s for %s %s", error_msg, request.method, request.path)
                messages.error(request, error_msg)
            # HTMX doesn't swap content for response codes >=400. However, we do want to show
            # the new messages, so we need to rewrite the response to 200, and make sure it only
            # swaps the oob notification content
            response = HttpResponse(
                headers={
                    "HX-Retarget": "#notification-messages .toast",
                    "HX-Reswap": "beforeend",
                }
            )
        response.write(loader.render_to_string(self.TEMPLATE, request=request))
        return response
