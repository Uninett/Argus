import logging

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.template import loader
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import force_str
from django_htmx.http import HttpResponseClientRedirect
from django.contrib import messages

from .request import HtmxHttpRequest

LOG = logging.getLogger(__name__)


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.public_urls = getattr(settings, "PUBLIC_URLS", ())
        self.login_url = force_str(settings.LOGIN_URL)
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
        response = redirect_to_login(request.get_full_path(), self.login_url, "next")
        if getattr(request, "htmx", False):
            response = HttpResponseClientRedirect(response.url)

        return response


class HtmxMessageMiddleware(MiddlewareMixin):
    """
    For htmx requests, adds messages to the #notification-messages div defined in
    `templates/messages/_notification_messages.html` using htmx's hx-swap-oob feature
    """

    TEMPLATE = "messages/_notification_messages_htmx_append.html"

    def process_exception(self, request, exception):
        error_msg = "500 Internal Server Error"
        messages.error(request, error_msg)
        if str(exception):
            error_msg = f"{error_msg}: {exception}"
        LOG.error(error_msg)
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
                error_msg = getattr(response, "content", b"")
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode("utf-8")
                if not error_msg:
                    error_msg = f"{response.status_code} {response.reason_phrase}"
                LOG.error("Unhandled exception: %s", error_msg)
                messages.error(request, "An unexpected error occured. Please try again")
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
