from django import forms

from argus.htmx.constants import (
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


class TimeframeForm(forms.Form):
    timeframe = forms.TypedChoiceField(
        required=False,
        choices=TIMEFRAME_CHOICES,
        coerce=int,
        initial=TIMEFRAME_DEFAULT,
        widget=IncidentListRefreshInfoSelect,
    )
