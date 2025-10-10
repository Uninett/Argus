from django.utils.decorators import method_decorator

from allauth.account.authentication import get_authentication_records
from allauth.account.internal.decorators import login_stage_required
from allauth.mfa.base.views import AuthenticateView as MFAAuthenticateView
from allauth.mfa.stages import AuthenticateStage


def is_socialaccount_login(request):
    for method in get_authentication_records(request):
        if method["method"] == "socialaccount":
            return True
    return False


@method_decorator(
    login_stage_required(stage=AuthenticateStage.key, redirect_urlname="account_login"),
    name="dispatch",
)
class ArgusMFAAuthenticateView(MFAAuthenticateView):
    def dispatch(self, request, *args, **kwargs):
        self.stage = request._login_stage
        if is_socialaccount_login(request):
            return self.stage.exit()
        return super().dispath(request, *args, **kwargs)
