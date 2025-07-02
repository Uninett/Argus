from datetime import timedelta

from django import forms
from django.utils.timezone import now as tznow

from argus.htmx.constants import (
    PAGE_SIZE_CHOICES,
    PAGE_SIZE_DEFAULT,
    TIMEFRAME_CHOICES,
    TIMEFRAME_DEFAULT,
)

# modals


class AckForm(forms.Form):
    description = forms.CharField()
    expiration = forms.DateTimeField(required=False)


class DescriptionOptionalForm(forms.Form):
    "For closing/reopening"

    description = forms.CharField(required=False)


class EditTicketUrlForm(forms.Form):
    ticket_url = forms.URLField(required=False)


class AddTicketUrlForm(forms.Form):
    ticket_url = forms.URLField(required=True)


# incident list filter widgets


class IncidentListRefreshInfoSelect(forms.Select):
    template_name = "htmx/components/incident_list_refresh_info_select.html"


# incident filter forms


class IncidentListForm(forms.Form):
    def get_clean_value(self):
        value = self.initial
        if self.is_bound and self.is_valid():
            value = self.cleaned_data[self.fieldname]
        return value

    def filter(self, queryset):
        return queryset


class PageNumberForm(IncidentListForm):
    fieldname = "page"
    field_initial = 1

    page = forms.IntegerField(required=False, initial=field_initial, min_value=field_initial)


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


## not stored


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

    def filter(self, queryset):
        timeframe = self.get_clean_value()
        if timeframe:
            after = tznow() - timedelta(seconds=timeframe * 60)
            queryset = queryset.filter(start_time__gte=after)
        return queryset
