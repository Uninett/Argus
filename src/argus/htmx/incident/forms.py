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


# incident filter, not stored


class TimeframeForm(forms.Form):
    timeframe = forms.TypedChoiceField(
        required=False,
        choices=TIMEFRAME_CHOICES,
        coerce=int,
        initial=TIMEFRAME_DEFAULT,
        widget=forms.Select(
            attrs={
                "class": "select select-xs bg-transparent text-base border-none -ml-2",
                "autocomplete": "off",
                "hx-get": ".",
                "hx-trigger": "change",
                "hx-target": "#table",
                "hx-swap": "outerHTML",
                "hx-push-url": "true",
                "hx-include": ".incident-list-param",
                "hx-indicator": "#incident-list .htmx-indicator",
            }
        ),
    )
