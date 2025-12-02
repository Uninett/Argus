import copy
import logging
from typing import Any, Optional, Dict

from django import forms
from django.middleware import csrf
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.timezone import now as tznow

from argus.auth.context_processors import preferences
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
from argus.htmx.incident.columns import get_default_column_layout_name, get_column_choices, get_incident_table_columns
from argus.incident.models import Incident


LOG = logging.getLogger(__name__)


class PreviewRadioSelect(forms.RadioSelect):
    option_template_name: str = "htmx/user/radio_option.html"

    def __init__(self, attrs=None, choices=(), previews=None):
        super().__init__(attrs)
        self.choices = choices
        self.previews = previews or dict()

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.attrs = self.attrs.copy()
        obj.choices = copy.copy(self.choices)
        obj.previews = copy.deepcopy(self.previews)
        memo[id(self)] = obj
        return obj

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        option["preview"] = self.previews.get(value, "")
        return option


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
    widget = PreviewRadioSelect
    template_name: str = "htmx/user/preference_field_form.html"
    widget_option_template_name: Optional[str] = None
    partial_response_template: Optional[str] = None
    widget_template_name: Optional[str] = None
    empty_message: Optional[str] = None
    preview_template_name = "htmx/user/_preference_choice_nopreview.html"

    def __init__(self, *args, **kwargs):
        """Configure field Form

        Set choices, initial and default lazily to ensure settings have loaded.
        Sends in CSRF token to the widget via "request".
        """
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

        self.csrf_token = csrf.get_token(self.request)
        self.choices = self.get_choices()
        self.default = self.get_default()
        self.fieldname = self.get_fieldname()
        self.preference = self.get_preference(self.request)
        self.initial = {self.fieldname: self.preference}
        self.previews = self.get_all_previews()
        if not self.choices:
            LOG.error("Preference choices for %s is malconfigured!", self.fieldname)

        self._configure_field()

    def _configure_field(self):
        self.field = self.fields[self.fieldname]
        self.fields[self.fieldname].choices = self.choices

        widget = self.widget(
            attrs={"csrf_token": self.csrf_token},
            choices=self.choices,
            previews=self.previews,
        )
        if self.widget_template_name:
            widget.template_name = self.widget_template_name
        if self.widget_option_template_name:
            widget.option_template_name = self.widget_option_template_name
        self.fields[self.fieldname].widget = widget

    def get_preview_context(self, choice: str) -> Dict[str, Any]:
        return {}

    def get_preview(self, choice: str) -> str:
        context = self.get_preview_context(choice)
        if not context:
            return ""
        preview = render_to_string(self.preview_template_name, context)
        return mark_safe(preview)

    def get_all_previews(self):
        previews = {}
        for choice, _ in self.choices:
            previews[choice] = self.get_preview(choice)
        return previews

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
    empty_message = "No datetime formats configured"
    preview_template_name = "htmx/user/_preference_choice_preview_datetime.html"
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

    def get_preview_context(self, choice: str) -> Dict[str, Any]:
        format = DATETIME_FORMATS.get(choice, None)
        context = {
            "timestamp": tznow(),
            "format": format,
        }
        return context


class IncidentsTableLayout(SimplePreferenceForm):
    "Preference for compactness of layout"

    label = "Incidents table layout"
    choices = INCIDENTS_TABLE_LAYOUT_CHOICES
    default = INCIDENTS_TABLE_LAYOUT_DEFAULT

    incidents_table_layout = forms.ChoiceField(required=False)


class IncidentsTableColumnForm(SimplePreferenceForm):
    "Preference for named column layout"

    label = "Table column preset"
    # preview_template_name = "htmx/incident/_unpaged_incident_table.html"
    incidents_table_column_name = forms.ChoiceField(required=False)

    @classmethod
    def get_choices(cls):
        cls.choices = get_column_choices()
        return cls.choices

    @classmethod
    def get_default(cls):
        cls.default = get_default_column_layout_name()
        return cls.default

    def get_preview_context(self, choice: str) -> Dict[str, Any]:
        columns = get_incident_table_columns(choice)
        pref_context = preferences(self.request)
        prefs = pref_context["preferences"]
        context = {
            "preferences": prefs,
            "incident_list": Incident.objects.all()[:1],
            "columns": columns,
            "dummy_column": True,
            "refresh_info_forms": {},
        }
        return context


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
    empty_message = "No themes configured"
    preview_template_name = "htmx/user/_preference_choice_preview_theme.html"

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

    def get_preview_context(self, choice: str) -> Dict[str, Any]:
        context = {
            "current_theme": choice,
            "theme_colors": [
                "bg-base-100",
                "bg-base-200",
                "bg-base-300",
                "bg-primary",
                "bg-secondary",
                "bg-accent",
                "bg-neutral",
                "bg-info",
                "bg-success",
                "bg-warning",
                "bg-error",
            ],
        }
        return context
