from django import forms
from django.contrib import messages
from django.urls import reverse
from django.views.generic import ListView

from argus.filter import get_filter_backend
from argus.incident.models import SourceSystem, Tag
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
    sourceSystemIds = forms.MultipleChoiceField(
        widget=BadgeDropdownMultiSelect(
            attrs={"placeholder": "select sources..."},
            partial_get=None,
        ),
        required=False,
        label="Sources",
    )
    tags = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "key=value, ...",
                "class": "input input-primary input-bordered input-sm overflow-y-auto min-h-8 h-auto max-h-16 max-w-xs leading-tight",
            }
        ),
        required=False,
        label="Tags",
        help_text='Press "Enter" after each completed tag',
    )
    maxlevel = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={"type": "range", "step": "1", "min": min(Level).value, "max": max(Level).value}
        ),
        label="Level <=",
        initial=max(Level).value,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # mollify tests
        self.fields["sourceSystemIds"].widget.partial_get = reverse("htmx:incident-filter")
        self.fields["sourceSystemIds"].choices = tuple(SourceSystem.objects.values_list("id", "name"))

    def clean_tags(self):
        tags = self.cleaned_data["tags"]
        if not tags:
            return None

        try:
            for tag in tags.split(","):
                Tag.split(tag.strip())
        except ValueError:
            raise forms.ValidationError("Tags need to have the format key=value, key2=value2")

        return tags

    def _tristate(self, onkey, offkey):
        on = self.cleaned_data.get(onkey, None)
        off = self.cleaned_data.get(offkey, None)
        if on == off:
            return None, None
        if on and not off:
            return True, False
        if off and not on:
            return False, True

    def to_filterblob(self):
        if not self.is_valid():
            return {}

        filterblob = {}

        open, closed = self._tristate("open", "closed")
        filterblob["open"] = open
        filterblob["closed"] = closed

        acked, unacked = self._tristate("acked", "unacked")
        filterblob["acked"] = acked
        filterblob["unacked"] = unacked

        sourceSystemIds = self.cleaned_data.get("sourceSystemIds", [])
        if sourceSystemIds:
            filterblob["sourceSystemIds"] = sourceSystemIds

        tags = self.cleaned_data.get("tags", [])
        if tags:
            filterblob["tags"] = [tag.strip() for tag in tags.split(",")]

        maxlevel = self.cleaned_data.get("maxlevel", 0)
        if maxlevel:
            filterblob["maxlevel"] = maxlevel

        return filterblob


class NamedFilterForm(forms.ModelForm):
    class Meta:
        model = Filter
        fields = ["name", "filter"]


class FilterListView(FilterMixin, ListView):
    pass


def incident_list_filter(request, qs):
    filter_pk, filter_obj = request.session.get("selected_filter", None), None
    if filter_pk:
        filter_obj = Filter.objects.get(pk=filter_pk)
    if filter_obj:
        filterblob = filter_obj.filter
        if "tags" in filterblob.keys():
            filterblob["tags"] = ", ".join(filterblob["tags"])
        form = IncidentFilterForm(filter_obj.filter)
    else:
        if request.method == "POST":
            form = IncidentFilterForm(request.POST)
        else:
            form = IncidentFilterForm(request.GET or None)

    if form.is_valid():
        filterblob = form.to_filterblob()
        qs = QuerySetFilter.filtered_incidents(filterblob, qs)
    else:
        for field, error_messages in form.errors.items():
            messages.error(request, f"{field}: {','.join(error_messages)}")
    return form, qs


def create_named_filter(request, filter_name: str, filterblob: dict):
    form = NamedFilterForm({"name": filter_name, "filter": filterblob})
    filter_obj = None

    if form.is_valid():
        filter_obj = Filter.objects.create(
            user=request.user, name=form.cleaned_data["name"], filter=form.cleaned_data["filter"]
        )
    return form, filter_obj
