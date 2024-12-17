from django import forms

from argus.filter import get_filter_backend
from argus.incident.models import SourceSystem
from argus.incident.constants import Level


filter_backend = get_filter_backend()
QuerySetFilter = filter_backend.QuerySetFilter


class ExtraWidgetMixin:
    def __init__(self, extra=None, **kwargs):
        super().__init__(**kwargs)
        self.extra = {} if extra is None else extra

    def __deepcopy__(self, memo):
        obj = super().__deepcopy__(memo)
        obj.extra = self.extra.copy()
        memo[id(self)] = obj
        return obj


class DropdownMultiSelect(ExtraWidgetMixin, forms.CheckboxSelectMultiple):
    template_name = "htmx/forms/dropdown_select_multiple.html"
    option_template_name = "htmx/forms/checkbox_select_multiple.html"


class IncidentFilterForm(forms.Form):
    open = forms.BooleanField(required=False)
    closed = forms.BooleanField(required=False)
    acked = forms.BooleanField(required=False)
    unacked = forms.BooleanField(required=False)
    source = forms.MultipleChoiceField(
        widget=DropdownMultiSelect(
            attrs={"placeholder": "select sources..."},
            extra={
                "hx_get": "htmx:incidents-filter",
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


def incident_list_filter(request, qs):
    # TODO: initialize with chosen Filter.filter if any
    form = IncidentFilterForm(request.GET or None)

    if form.is_valid():
        filterblob = form.to_filterblob()
        qs = QuerySetFilter.filtered_incidents(filterblob, qs)
    return form, qs
