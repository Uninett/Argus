from datetime import timedelta

from django import forms
from django.utils.timezone import now as tznow

from argus.htmx.constants import (
    PAGE_SIZE_CHOICES,
    PAGE_SIZE_DEFAULT,
    TIMEFRAME_CHOICES,
    TIMEFRAME_DEFAULT,
)
from argus.htmx.incident.forms.base import IncidentListForm, SearchMixin, HasTextSearchMixin
from argus.incident.constants import Level


SORT_ORDER_CHOICES = [
    ("asc", "Ascending"),
    ("desc", "Descending"),
]
SORT_ORDER_DEFAULT = "desc"
SORT_DEFAULT = "start_time"


# incident list filter widgets


class IncidentListRefreshInfoSelect(forms.Select):
    template_name = "htmx/components/incident_list_refresh_info_select.html"


# incident filter forms


class PageNumberForm(IncidentListForm):
    fieldname = "page"
    field_initial = 1

    page = forms.IntegerField(required=False, initial=field_initial, min_value=field_initial)


# column search, not stored
class IdForm(SearchMixin, IncidentListForm):
    widget_template_name = "htmx/incident/cells/search_fields/input_search.html"
    fieldname = "id"
    field_initial = ""
    lookup = fieldname
    placeholder = "ID"

    id = forms.IntegerField(required=False)


class DescriptionForm(SearchMixin, IncidentListForm):
    widget_template_name = "htmx/incident/cells/search_fields/input_search.html"
    fieldname = "description"
    field_initial = ""
    lookup = f"{fieldname}__contains"
    placeholder = "part of description"

    description = forms.CharField(required=False)


class LevelForm(SearchMixin, IncidentListForm):
    fieldname = "level"
    field_initial = ""
    widget_classes = "incident-list-param"
    lookup = f"{fieldname}__in"

    level = forms.TypedMultipleChoiceField(
        required=False,
        choices=Level,
        coerce=int,
        empty_value="",
    )


class HasTicketForm(HasTextSearchMixin, IncidentListForm):
    widget_classes = "incident-list-param"
    fieldname = "has_ticket"
    field_initial = ""
    lookup = "ticket_url"

    has_ticket = forms.ChoiceField(
        required=False,
        choices=[("yes", "Yes"), ("no", "No"), ("", "N/A")],
        widget=forms.RadioSelect,
    )


class FindTicketForm(SearchMixin, IncidentListForm):
    widget_template_name = "htmx/incident/cells/search_fields/input_search.html"
    fieldname = "ticket_url"
    field_initial = ""
    lookup = f"{fieldname}__contains"
    placeholder = "part of ticket url"

    ticket_url = forms.CharField(required=False)


# Stored in preference
class PageSizeForm(IncidentListForm):
    fieldname = "page_size"
    field_initial = PAGE_SIZE_DEFAULT

    page_size = forms.TypedChoiceField(
        required=False,
        choices=PAGE_SIZE_CHOICES,
        coerce=int,
        initial=field_initial,
        widget=IncidentListRefreshInfoSelect,
    )

    # page_size is used by a paginator, no need to define ``filter``

    def __init__(self, data=None, *args, **kwargs):
        # Only bind the form if page_size is actually in the data.
        # This ensures the stored preference is used for rendering when
        # page_size is not in the URL.
        if data is not None and self.fieldname not in data:
            data = None
        super().__init__(data, *args, **kwargs)

    def get_clean_value(self, request):
        # breakpoint()
        if request.GET.get(self.fieldname, 0):
            return super().get_clean_value(request)
        return self.get_initial_value(request)

    @classmethod
    def get_initial_value(cls, request):
        return cls._get_initial_preference_value(request, "argus_htmx")

    def store(self, request):
        # Only store the preference if page_size was explicitly provided in the request
        if not request.GET.get(self.fieldname):
            return None
        return self._store_preference(request, "argus_htmx")


# Stored in session to ensure it does not go missing
class TimeframeForm(IncidentListForm):
    fieldname = "timeframe"
    field_initial = TIMEFRAME_DEFAULT

    timeframe = forms.TypedChoiceField(
        required=False,
        choices=TIMEFRAME_CHOICES,
        coerce=int,
        initial=field_initial,
        widget=IncidentListRefreshInfoSelect,
    )

    def filter(self, queryset, request):
        timeframe = self.get_clean_value(request)
        if timeframe:
            after = tznow() - timedelta(minutes=timeframe)
            queryset = queryset.filter(start_time__gte=after)
        return queryset

    @classmethod
    def get_initial_value(cls, request):
        return request.session.get("timeframe", cls.field_initial) or cls.field_initial

    def store(self, request):
        return self._store_in_session(request)


class SortForm(forms.Form):
    """Form for handling column sorting parameters.

    Manages two fields:
    - sort: the column/field to sort by
    - sort_order: ascending or descending
    """

    # Allowlist of valid sort fields to prevent arbitrary field access
    ALLOWED_SORT_FIELDS = {
        "pk",
        "start_time",
        "end_time",
        "level",
        "source__name",
        "source__type__name",
        "description",
        "ticket_url",
    }

    sort = forms.CharField(required=False, initial=SORT_DEFAULT)
    sort_order = forms.ChoiceField(
        required=False,
        choices=SORT_ORDER_CHOICES,
        initial=SORT_ORDER_DEFAULT,
    )

    def get_sort_field(self):
        """Return the field to sort by, validated against allowlist."""
        if self.is_valid():
            sort_field = self.cleaned_data.get("sort") or SORT_DEFAULT
            # Validate against allowlist to ignore unsupported fields
            if sort_field in self.ALLOWED_SORT_FIELDS:
                return sort_field
        return SORT_DEFAULT

    def get_sort_order(self):
        """Return the sort order (asc/desc)."""
        if self.is_valid():
            return self.cleaned_data.get("sort_order") or SORT_ORDER_DEFAULT
        return SORT_ORDER_DEFAULT

    def get_ordering(self):
        """Return the Django ORM ordering string (e.g., '-start_time')."""
        sort_field = self.get_sort_field()
        sort_order = self.get_sort_order()
        if sort_order == "desc":
            return f"-{sort_field}"
        return sort_field

    def is_default_sort_field(self):
        """Check if the current sort field is the default."""
        return self.get_sort_field() == SORT_DEFAULT
