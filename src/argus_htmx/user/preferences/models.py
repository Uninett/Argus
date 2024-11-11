from django import forms

from argus.auth.models import Preferences, preferences_manager_factory

from argus_htmx.constants import (
    DATETIME_FORMATS,
    DATETIME_DEFAULT,
    DATETIME_CHOICES,
    PAGE_SIZE_CHOICES,
    DEFAULT_PAGE_SIZE,
    THEME_CHOICES,
)


class DateTimeFormatForm(forms.Form):
    datetime_format_name = forms.ChoiceField(required=False, choices=DATETIME_CHOICES)

    def clean_datetime_format_name(self):
        return self.cleaned_data.get("datetime_format_name", DATETIME_DEFAULT) or DATETIME_DEFAULT


class PageSizeForm(forms.Form):
    page_size = forms.TypedChoiceField(required=False, choices=PAGE_SIZE_CHOICES, coerce=int)

    def clean_page_size(self):
        return self.cleaned_data.get("page_size", DEFAULT_PAGE_SIZE) or DEFAULT_PAGE_SIZE


class ThemeForm(forms.Form):
    theme = forms.ChoiceField(choices=THEME_CHOICES)


class ArgusHtmxPreferences(Preferences):
    _namespace = "argus_htmx"
    FORMS = {
        "datetime_format_name": DateTimeFormatForm,
        "page_size": PageSizeForm,
        "theme": ThemeForm,
    }
    _FIELD_DEFAULTS = {
        "datetime_format_name": DATETIME_DEFAULT,
        "page_size": DEFAULT_PAGE_SIZE,
    }

    class Meta:
        proxy = True

    objects = preferences_manager_factory(_namespace)()

    def update_context(self, context):
        datetime_format_name = context.get("datetime_format_name", DATETIME_DEFAULT)
        datetime_format = DATETIME_FORMATS[datetime_format_name]
        return {"datetime_format": datetime_format}
