from django import forms

from argus.auth.models import PreferenceField, preferences
from argus.htmx.constants import (
    DATETIME_CHOICES,
    DATETIME_DEFAULT,
    DATETIME_FORMATS,
    INCIDENTS_TABLE_LAYOUT_CHOICES,
    INCIDENTS_TABLE_LAYOUT_DEFAULT,
    PAGE_SIZE_DEFAULT,
    PAGE_SIZE_CHOICES,
    THEME_CHOICES,
    THEME_DEFAULT,
    THEME_NAMES,
    UPDATE_INTERVAL_DEFAULT,
    UPDATE_INTERVAL_CHOICES,
)
from argus.htmx.incident.utils import update_interval_string


class DateTimeFormatForm(forms.Form):
    datetime_format_name = forms.ChoiceField(required=False, choices=DATETIME_CHOICES)


class IncidentsTableLayout(forms.Form):
    incidents_table_layout = forms.ChoiceField(required=False, choices=INCIDENTS_TABLE_LAYOUT_CHOICES)


class PageSizeForm(forms.Form):
    page_size = forms.TypedChoiceField(required=False, choices=PAGE_SIZE_CHOICES, coerce=int)


class UpdateIntervalForm(forms.Form):
    update_interval = forms.TypedChoiceField(
        required=False, choices=UPDATE_INTERVAL_CHOICES, coerce=lambda v: "never" if v.lower() == "never" else int(v)
    )


class ThemeForm(forms.Form):
    theme = forms.ChoiceField(choices=THEME_CHOICES)


@preferences(namespace="argus_htmx")
class ArgusHtmxPreferences:
    FIELDS = {
        "datetime_format_name": PreferenceField(
            form=DateTimeFormatForm, default=DATETIME_DEFAULT, choices=DATETIME_FORMATS
        ),
        "page_size": PreferenceField(form=PageSizeForm, default=PAGE_SIZE_DEFAULT, choices=PAGE_SIZE_CHOICES),
        "theme": PreferenceField(
            form=ThemeForm,
            default=THEME_DEFAULT,
            choices=THEME_NAMES,
            partial_response_template="htmx/user/_current_theme.html",
        ),
        "update_interval": PreferenceField(
            form=UpdateIntervalForm, default=UPDATE_INTERVAL_DEFAULT, choices=UPDATE_INTERVAL_CHOICES
        ),
        "incidents_table_layout": PreferenceField(
            form=IncidentsTableLayout, default=INCIDENTS_TABLE_LAYOUT_DEFAULT, choices=INCIDENTS_TABLE_LAYOUT_CHOICES
        ),
    }

    def update_context(self, context):
        datetime_format_name = context.get("datetime_format_name", DATETIME_DEFAULT)
        datetime_format = DATETIME_FORMATS[datetime_format_name]
        incidents_table_layout = context.get("incidents_table_layout", INCIDENTS_TABLE_LAYOUT_DEFAULT)
        update_interval = context.get("update_interval", UPDATE_INTERVAL_DEFAULT)
        return {
            "datetime_format": datetime_format.datetime,
            "date_format": datetime_format.date,
            "time_format": datetime_format.time,
            "incidents_table_layout_compact": incidents_table_layout == "compact",
            "update_interval_pp": update_interval_string(update_interval),
        }
