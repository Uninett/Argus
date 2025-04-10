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


# incident filter, not stored


# look and feel and magic

QUERYPARAM_WIDGET_CLASSES = "select select-xs bg-transparent text-base border-none -ml-2"
QUERYPARAM_HX_ATTRS = {
    "hx-get": ".",
    "hx-trigger": "change",
    "hx-target": "#table",
    "hx-swap": "outerHTML",
    "hx-push-url": "true",
    "hx-include": ".incident-list-param",
    "hx-indicator": "#incident-list .htmx-indicator",
}
QUERYPARAM_WIDGET_ATTRS = {"autocomplete": "off", "class": QUERYPARAM_WIDGET_CLASSES}
QUERYPARAM_WIDGET_ATTRS.update(QUERYPARAM_HX_ATTRS)


class PageSizeForm(forms.Form):
    page_size = forms.TypedChoiceField(
        required=False,
        choices=PAGE_SIZE_CHOICES,
        coerce=int,
        initial=PAGE_SIZE_DEFAULT,
        widget=forms.Select(attrs=QUERYPARAM_WIDGET_ATTRS),
    )


class TimeframeForm(forms.Form):
    timeframe = forms.TypedChoiceField(
        required=False,
        choices=TIMEFRAME_CHOICES,
        coerce=int,
        initial=TIMEFRAME_DEFAULT,
        widget=forms.Select(attrs=QUERYPARAM_WIDGET_ATTRS),
    )
