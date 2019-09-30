from django.http import HttpResponseRedirect
from django.views.generic import FormView

from . import json_utils
from .forms import AlertJsonForm


class CreateAlertView(FormView):
    template_name = "alert/create_alert.html"
    form_class = AlertJsonForm

    def form_valid(self, form):
        json_string = form.cleaned_data['json']
        alert_hist = json_utils.json_to_alert_hist(json_string)
        alert_hist.save()
        # Redirect back to same form page
        return HttpResponseRedirect(self.request.path_info)
