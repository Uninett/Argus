from argus.auth.models import preferences
from argus.htmx.dateformat.constants import DATETIME_FORMATS
from argus.htmx.constants import (
    INCIDENTS_TABLE_LAYOUT_DEFAULT,
    UPDATE_INTERVAL_DEFAULT,
)
from argus.htmx.incident.utils import update_interval_string
from argus.htmx.themes.utils import resolve_theme_name
from .forms import (
    DateTimeFormatForm,
    IncidentFilterPreferenceForm,
    IncidentsTableLayout,
    IncidentsTableColumnForm,
    PageSizeForm,
    UpdateIntervalForm,
    ThemeForm,
)


@preferences(namespace="argus_htmx")
class ArgusHtmxPreferences:
    FIELDS = {
        "datetime_format_name": DateTimeFormatForm.get_preference_field(),
        "page_size": PageSizeForm.get_preference_field(),
        "theme": ThemeForm.get_preference_field(),
        "update_interval": UpdateIntervalForm.get_preference_field(),
        "incidents_table_layout": IncidentsTableLayout.get_preference_field(),
        "incidents_table_column_name": IncidentsTableColumnForm.get_preference_field(),
        "incident_filter": IncidentFilterPreferenceForm.get_preference_field(),
    }

    def update_context(self, context):
        # Resolve deprecated theme names (e.g. "sikt" → "light")
        theme = context.get("theme")
        if theme:
            context["theme"] = resolve_theme_name(theme)

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
