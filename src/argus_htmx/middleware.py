from django.conf import settings
from django.contrib.auth.views import redirect_to_login
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
        return redirect_to_login(request.get_full_path(), self.login_url, "next")
