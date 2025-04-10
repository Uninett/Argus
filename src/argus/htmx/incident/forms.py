from django import forms

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


# incident filter, not stored


class PageSizeForm(forms.Form):
    page_size = forms.TypedChoiceField(
        required=False,
        choices=PAGE_SIZE_CHOICES,
        coerce=int,
        initial=PAGE_SIZE_DEFAULT,
        widget=IncidentListRefreshInfoSelect,
    )


class TimeframeForm(forms.Form):
    timeframe = forms.TypedChoiceField(
        required=False,
        choices=TIMEFRAME_CHOICES,
        coerce=int,
        initial=TIMEFRAME_DEFAULT,
        widget=IncidentListRefreshInfoSelect,
    )
