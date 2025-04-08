from django import forms
from django.contrib import messages
from django.urls import reverse
from django.views.generic import ListView

from argus.filter import get_filter_backend
from argus.htmx.widgets import BadgeDropdownMultiSelect
from argus.incident.constants import AckedStatus, Level, OpenStatus
from argus.incident.models import SourceSystem, Tag
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
    open = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={"type": "range", "step": "1", "min": min(OpenStatus).value, "max": max(OpenStatus).value}
        ),
        label="Open State",
        initial=OpenStatus.BOTH.value,
        required=False,
    )
    acked = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={"type": "range", "step": "1", "min": min(AckedStatus).value, "max": max(AckedStatus).value}
        ),
        label="Acked",
        initial=AckedStatus.BOTH.value,
        required=False,
    )
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

    EMPTY_FILTERBLOB = {
        "open": None,
        "acked": None,
        "sourceSystemIds": [],
        "tags": "",
        "maxlevel": max(Level).value,
    }

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

    def _open_tristate(self):
        """Returns True if incidents should be open, False if they should be closed
        and None if both should be shown
        """
        open_status = self.cleaned_data.get("open", None)
        if open_status == OpenStatus.OPEN:
            return True
        elif open_status == OpenStatus.CLOSED:
            return False
        else:
            return None

    def _acked_tristate(self):
        """Returns True if incidents should be acked, False if they should be unacked
        and None if both should be shown
        """
        acked_status = self.cleaned_data.get("acked", None)
        if acked_status == AckedStatus.ACKED:
            return True
        elif acked_status == AckedStatus.UNACKED:
            return False
        else:
            return None

    def to_filterblob(self):
        if not self.is_valid():
            return {}

        filterblob = {}

        filterblob["open"] = self._open_tristate()

        filterblob["acked"] = self._acked_tristate()

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


def incident_list_filter(request, qs, use_empty_filter=False):
    filter_pk, filter_obj = request.session.get("selected_filter", None), None
    if filter_pk:
        filter_obj = Filter.objects.get(pk=filter_pk)
    if filter_obj:
        form = IncidentFilterForm(_convert_filterblob(filter_obj.filter))
    else:
        if request.method == "POST":
            form = IncidentFilterForm(request.POST)
        else:
            if use_empty_filter:
                filterblob = IncidentFilterForm.EMPTY_FILTERBLOB
                form = IncidentFilterForm(filterblob)
            else:
                form = IncidentFilterForm(request.GET or None)

    if form.is_valid():
        filterblob = form.to_filterblob()
        qs = QuerySetFilter.filtered_incidents(filterblob, qs)
    else:
        for field, error_messages in form.errors.items():
            messages.error(request, f"{field}: {','.join(error_messages)}")
    return form, qs


def _convert_filterblob(filterblob):
    """Converts values in filterblob so it can be used as valid input for IncidentFilterForm"""
    if "tags" in filterblob.keys():
        filterblob["tags"] = ", ".join(filterblob["tags"])

    if "open" in filterblob.keys():
        open_state = filterblob["open"]
        if open_state is True:
            filterblob["open"] = OpenStatus.OPEN
        elif open_state is False:
            filterblob["open"] = OpenStatus.CLOSED
        else:
            filterblob["open"] = OpenStatus.BOTH

    if "acked" in filterblob.keys():
        acked_state = filterblob["acked"]
        if acked_state is True:
            filterblob["acked"] = AckedStatus.ACKED
        elif acked_state is False:
            filterblob["acked"] = AckedStatus.UNACKED
        else:
            filterblob["acked"] = AckedStatus.BOTH

    return filterblob


def create_named_filter(request, filter_name: str, filterblob: dict):
    form = NamedFilterForm({"name": filter_name, "filter": filterblob})
    filter_obj = None

    if form.is_valid():
        filter_obj = Filter.objects.create(
            user=request.user, name=form.cleaned_data["name"], filter=form.cleaned_data["filter"]
        )
    return form, filter_obj
