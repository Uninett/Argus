import json

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.contrib.messages import get_messages
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import force_str


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
        return redirect_to_login(request.get_full_path(), self.login_url, 'next')


class HtmxMessageMiddleware(MiddlewareMixin):
    """
    Add messages to HX-Trigger header if request was via HTMX
    """

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:

        # The HX-Request header indicates that the request was made with HTMX
        if "HX-Request" not in request.headers:
            return response

        # Ignore redirections because HTMX cannot read the headers
        if 300 <= response.status_code < 400:
            return response

        # Extract the messages
        messages = [
            {"message": message.message, "tags": message.tags}
            for message in get_messages(request)
        ]
        if not messages:
            return response

        # Get the existing HX-Trigger that could have been defined by the view
        hx_trigger = response.headers.get("HX-Trigger")

        if hx_trigger is None:
            # If the HX-Trigger is not set, start with an empty object
            hx_trigger = {}
        elif hx_trigger.startswith("{"):
            # If the HX-Trigger uses the string syntax, convert to the object syntax
            hx_trigger = json.loads(hx_trigger)
        else:
            # If the HX-Trigger uses the object syntax, parse the object
            hx_trigger = {hx_trigger: True}

        # Add the messages array in the HX-Trigger object
        hx_trigger["messages"] = messages

        # Add or update the HX-Trigger
        response.headers["HX-Trigger"] = json.dumps(hx_trigger)

        return response
