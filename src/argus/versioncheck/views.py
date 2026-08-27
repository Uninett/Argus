import logging
from datetime import timedelta

from django import forms
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now
from django.views.decorators.http import require_POST

from .utils import get_latest_registered_version, register_and_return_latest_version

LOG = logging.getLogger(__name__)


class ParamForm(forms.Form):
    next = forms.CharField()


@require_POST
def check_for_new_version(request):
    latest_registered = get_latest_registered_version()
    if not latest_registered or latest_registered.upload_time < now() - timedelta(hours=12):
        LOG.info("Checking for new version of argus")
        register_and_return_latest_version()

    params = ParamForm(request.GET)
    if params.is_valid():
        next = params.cleaned_data["next"]
    else:
        next = reverse("about")

    return redirect(to=next)
