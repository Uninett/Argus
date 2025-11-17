from typing import Any

from django import forms

from argus.auth.models import PreferenceField, preferences
from argus.htmx.themes.utils import get_theme_default, get_theme_names
from argus.htmx.dateformat.constants import DATETIME_FORMATS, get_datetime_format_default
from argus.htmx.constants import (
    INCIDENTS_TABLE_LAYOUT_CHOICES,
    INCIDENTS_TABLE_LAYOUT_DEFAULT,
    PAGE_SIZE_DEFAULT,
    PAGE_SIZE_CHOICES,
    UPDATE_INTERVAL_DEFAULT,
    UPDATE_INTERVAL_CHOICES,
)
from argus.htmx.incident.columns import get_column_choices, get_default_column_layout_name
from argus.htmx.incident.utils import update_interval_string


class SimplePreferenceForm(forms.Form):
    choices: list
    default: Any

    def __init__(self, *args, **kwargs):
        "Set choices lazily to ensure everything has loaded"
        super().__init__(*args, **kwargs)
        choices = self.get_choices()
        self.fieldname = self.get_fieldname()
        self.fields[self.fieldname].choices = choices

    @classmethod
    def get_preference_field(cls):
        "Generate and return a PreferenceField"
        kwargs = {"choices": cls.get_choices(), "default": cls.get_default(), "form": cls}
        if hasattr(cls, "partial_response_template"):
            kwargs["partial_response_template"] = cls.partial_response_template
        return PreferenceField(**kwargs)

    @classmethod
    def get_fieldname(cls):
        "Get fieldname of form, preferrably the same as the preference name"

        return tuple(cls.declared_fields.keys())[0]

    @classmethod
    def get_choices(cls):
        """Return something suitable for formfield.choices

        Override if the choices are derived from a django setting.
        """
        return cls.choices

    @classmethod
    def get_default(cls):
        """Return something suitable for the fallback default

        Override if the default is defined in a django setting.
        """
        return cls.default


class DateTimeFormatForm(SimplePreferenceForm):
    datetime_format_name = forms.ChoiceField(required=False)

    @classmethod
    def get_choices(cls):
        formats = DATETIME_FORMATS
        choices = tuple((name, name) for name in formats)
        return choices

    @classmethod
    def get_default(cls):
        default = get_datetime_format_default()
        return default


class IncidentsTableLayout(SimplePreferenceForm):
    "Preference for compactness of layout"

    choices = INCIDENTS_TABLE_LAYOUT_CHOICES
    default = INCIDENTS_TABLE_LAYOUT_DEFAULT

    incidents_table_layout = forms.ChoiceField(required=False)


class IncidentsTableColumnForm(SimplePreferenceForm):
    "Preference for named column layout"

    incidents_table_column_name = forms.ChoiceField(required=False)

    @classmethod
    def get_choices(cls):
        cls.choices = get_column_choices()
        return cls.choices

    @classmethod
    def get_default(cls):
        cls.default = get_default_column_layout_name()
        return cls.default


class PageSizeForm(SimplePreferenceForm):
    choices = PAGE_SIZE_CHOICES
    default = PAGE_SIZE_DEFAULT

    page_size = forms.TypedChoiceField(required=False, coerce=int)


class UpdateIntervalForm(SimplePreferenceForm):
    choices = UPDATE_INTERVAL_CHOICES
    default = UPDATE_INTERVAL_DEFAULT

    update_interval = forms.TypedChoiceField(
        required=False, coerce=lambda v: "never" if v.lower() == "never" else int(v)
    )


class ThemeForm(SimplePreferenceForm):
    partial_response_template = "htmx/user/_current_theme.html"

    theme = forms.ChoiceField()

    @classmethod
    def get_choices(cls):
        names = sorted(get_theme_names())
        choices = tuple((theme, theme) for theme in names)
        return choices

    @classmethod
    def get_default(cls):
        return get_theme_default()


@preferences(namespace="argus_htmx")
class ArgusHtmxPreferences:
    FIELDS = {
        "datetime_format_name": DateTimeFormatForm.get_preference_field(),
        "page_size": PageSizeForm.get_preference_field(),
        "theme": ThemeForm.get_preference_field(),
        "update_interval": UpdateIntervalForm.get_preference_field(),
        "incidents_table_layout": IncidentsTableLayout.get_preference_field(),
        "incidents_table_column_name": IncidentsTableColumnForm.get_preference_field(),
    }

    def update_context(self, context):
        datetime_format_name = context.get("datetime_format_name", self.FIELDS["datetime_format_name"].default)
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
