from django import forms
from django.urls import reverse
from django.views.generic import ListView

from argus.filter import get_filter_backend
from argus.incident.models import SourceSystem
from argus.incident.constants import Level
from argus.htmx.widgets import BadgeDropdownMultiSelect
from argus.notificationprofile.models import Filter

filter_backend = get_filter_backend()
QuerySetFilter = filter_backend.QuerySetFilter

class FilterMixin:
    model = Filter

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user_id=self.request.user.id)

    def get_template_names(self):
        orig_app_label = self.model._meta.app_label
        orig_model_name = self.model._meta.model_name
        self.model._meta.app_label = "htmx/incident"
        self.model._meta.model_name = "filter"
        templates = super().get_template_names()
        self.model._meta.app_label = orig_app_label
        self.model._meta.model_name = orig_model_name
        return templates

    def get_success_url(self):
        return reverse("htmx:filter-list")



class IncidentFilterForm(forms.Form):
    open = forms.BooleanField(required=False)
    closed = forms.BooleanField(required=False)
    acked = forms.BooleanField(required=False)
    unacked = forms.BooleanField(required=False)
    source = forms.MultipleChoiceField(
        widget=BadgeDropdownMultiSelect(
            attrs={"placeholder": "select sources..."},
            extra={
                "hx_get": "htmx:incident-filter",
            },
        ),
        choices=tuple(SourceSystem.objects.values_list("id", "name")),
        required=False,
        label="Sources",
    )
    maxlevel = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={"type": "range", "step": "1", "min": min(Level).value, "max": max(Level).value}
        ),
        label="Level <=",
        initial=max(Level).value,
        required=False,
    )

    def _tristate(self, onkey, offkey):
        on = self.cleaned_data.get(onkey, None)
        off = self.cleaned_data.get(offkey, None)
        if on == off:
            return None
        if on and not off:
            return True
        if off and not on:
            return False

    def to_filterblob(self):
        if not self.is_valid():
            return {}

        filterblob = {}

        open = self._tristate("open", "closed")
        if open is not None:
            filterblob["open"] = open

        acked = self._tristate("acked", "unacked")
        if acked is not None:
            filterblob["acked"] = acked

        source = self.cleaned_data.get("source", [])
        if source:
            filterblob["sourceSystemIds"] = source

        maxlevel = self.cleaned_data.get("maxlevel", 0)
        if maxlevel:
            filterblob["maxlevel"] = maxlevel

        return filterblob


class FilterListView(FilterMixin, ListView):
    pass


def incident_list_filter(request, qs):
    # TODO: initialize with chosen Filter.filter if any
    form = IncidentFilterForm(request.GET or None)

    if form.is_valid():
        filterblob = form.to_filterblob()
        qs = QuerySetFilter.filtered_incidents(filterblob, qs)
    return form, qs
