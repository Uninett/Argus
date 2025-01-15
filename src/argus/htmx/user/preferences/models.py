from django import forms

from argus.auth.models import PreferenceField, preferences
from argus.htmx.constants import (
    ALLOWED_PAGE_SIZES,
    DATETIME_CHOICES,
    DATETIME_DEFAULT,
    DATETIME_FORMATS,
    DEFAULT_PAGE_SIZE,
    PAGE_SIZE_CHOICES,
    THEME_CHOICES,
    THEME_DEFAULT,
    THEME_NAMES,
)


class DateTimeFormatForm(forms.Form):
    datetime_format_name = forms.ChoiceField(required=False, choices=DATETIME_CHOICES)


class PageSizeForm(forms.Form):
    page_size = forms.TypedChoiceField(required=False, choices=PAGE_SIZE_CHOICES, coerce=int)


class ThemeForm(forms.Form):
    theme = forms.ChoiceField(choices=THEME_CHOICES)


@preferences(namespace="argus_htmx")
class ArgusHtmxPreferences:
    FIELDS = {
        "datetime_format_name": PreferenceField(
            form=DateTimeFormatForm, default=DATETIME_DEFAULT, choices=DATETIME_FORMATS
        ),
        "page_size": PreferenceField(form=PageSizeForm, default=DEFAULT_PAGE_SIZE, choices=ALLOWED_PAGE_SIZES),
        "theme": PreferenceField(
            form=ThemeForm,
            default=THEME_DEFAULT,
            choices=THEME_NAMES,
            partial_response_template="htmx/user/_current_theme.html",
        ),
    }

    def update_context(self, context):
        datetime_format_name = context.get("datetime_format_name", DATETIME_DEFAULT)
        datetime_format = DATETIME_FORMATS[datetime_format_name]
        return {
            "datetime_format": datetime_format.datetime,
            "date_format": datetime_format.date,
            "time_format": datetime_format.time,
        }
