import logging
from typing import Any, Optional

from django import forms
from django.middleware import csrf

from argus.auth.models import PreferenceField
from argus.auth.utils import get_preference
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
from argus.htmx.incident.columns import get_default_column_layout_name, get_column_choices


LOG = logging.getLogger(__name__)


class ClassicPreferenceFormMixin:
    def __init__(self, *args, **kwargs):
        """Configure field Form

        Remove the passed-in request, for preferences that do not depend on
        a set of choices.
        """
        kwargs.pop("request", None)
        super().__init__(*args, **kwargs)


class SimplePreferenceForm(forms.Form):
    choices: list
    default: Any
    label: str
    widget = forms.RadioSelect
    template_name: str = "htmx/user/preference_field_form.html"
    widget_option_template_name: str = "htmx/user/radio_option.html"
    widget_template_name: Optional[str] = None

    def __init__(self, *args, **kwargs):
        """Configure field Form

        Set choices, initial and default lazily to ensure settings have loaded.
        Sends in CSRF token to the widget via "request".
        """
        request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

        self.csrf_token = csrf.get_token(request)
        self.choices = self.get_choices()
        self.default = self.get_default()
        self.fieldname = self.get_fieldname()
        self.preference = self.get_preference(request)
        self.initial = {self.fieldname: self.preference}
        if not self.choices:
            LOG.error("Preference choices for %s is malconfigured!", self.fieldname)

        self._configure_field()

    def _configure_field(self):
        self.field = self.fields[self.fieldname]
        self.fields[self.fieldname].choices = self.choices

        if self.widget_template_name:
            self.widget.template_name = self.widget_template_name
        self.widget.option_template_name = self.widget_option_template_name

        widget = self.widget(
            attrs={"csrf_token": self.csrf_token},
            choices=self.choices,
        )
        self.fields[self.fieldname].widget = widget

    @classmethod
    def get_preference(cls, request):
        preference = get_preference(request, "argus_htmx", cls.get_fieldname())
        return preference

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
    label = "Date format"
    empty_message = "No datetime formats configured!?"

    datetime_format_name = forms.ChoiceField(required=False)

    @classmethod
    def get_choices(cls):
        formats = DATETIME_FORMATS
        cls.choices = tuple((name, name) for name in formats)
        return cls.choices

    @classmethod
    def get_default(cls):
        cls.default = get_datetime_format_default()
        return cls.default


class IncidentsTableLayout(SimplePreferenceForm):
    "Preference for compactness of layout"

    label = "Incidents table layout"
    choices = INCIDENTS_TABLE_LAYOUT_CHOICES
    default = INCIDENTS_TABLE_LAYOUT_DEFAULT

    incidents_table_layout = forms.ChoiceField(required=False)


class IncidentsTableColumnForm(SimplePreferenceForm):
    "Preference for named column layout"

    label = "Incidents table column setup"

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
    label = "Page size"
    choices = PAGE_SIZE_CHOICES
    default = PAGE_SIZE_DEFAULT

    page_size = forms.TypedChoiceField(required=False, coerce=int)


class UpdateIntervalForm(SimplePreferenceForm):
    label = "Update interval"
    choices = UPDATE_INTERVAL_CHOICES
    default = UPDATE_INTERVAL_DEFAULT

    update_interval = forms.TypedChoiceField(
        required=False, coerce=lambda v: "never" if v.lower() == "never" else int(v)
    )


class ThemeForm(SimplePreferenceForm):
    label = "Theme"
    partial_response_template = "htmx/user/_current_theme.html"

    theme = forms.ChoiceField()

    @classmethod
    def get_choices(cls):
        names = sorted(get_theme_names())
        cls.choices = tuple((theme, theme) for theme in names)
        return cls.choices

    @classmethod
    def get_default(cls):
        cls.default = get_theme_default()
        return cls.default
