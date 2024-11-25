"""
Definitions and defaults for UI customization on the incidents page.

Currently customizable UI elements:
- table columns: configure what columns to show in the incidents listing
"""

from dataclasses import dataclass
from typing import List, Optional, Union

from django.conf import settings

from argus_htmx import settings as argus_htmx_settings


@dataclass
class IncidentTableColumn:
    """Class for defining a column in the incidents table.

    :param name: identifier for this column
    :param label: what to show as the column header
    :param cell_template: template to use when rendering a cell for this column
    :param context: additional context to pass to the rendering cell. Will be made
        available as ``cell_context`` in the cell template
    """

    name: str  # identifier
    label: str  # display value
    cell_template: str
    header_template: Optional[str] = None
    context: Optional[dict] = None


_BUILTIN_COLUMN_LIST = [
    IncidentTableColumn(
        "row_select",
        "Selected",
        "htmx/incidents/_incident_checkbox.html",
        "htmx/incidents/_selected_incidents_header.html",
    ),
    IncidentTableColumn("id", "ID", "htmx/incidents/_incident_pk.html"),
    IncidentTableColumn(
        "start_time",
        "Timestamp",
        "htmx/incidents/_incident_start_time.html",
        "htmx/incidents/_incident_start_time_header.html",
    ),
    IncidentTableColumn("status", "Status", "htmx/incidents/_incident_status.html"),
    IncidentTableColumn("level", "Severity level", "htmx/incidents/_incident_level.html"),
    IncidentTableColumn("source", "Source", "htmx/incidents/_incident_source.html"),
    IncidentTableColumn("description", "Description", "htmx/incidents/_incident_description.html"),
    IncidentTableColumn("ack", "Ack", "htmx/incidents/_incident_ack.html"),
    IncidentTableColumn("combined_status", "Status", "htmx/incidents/_incident_combined_status.html"),
    IncidentTableColumn("ticket", "Ticket", "htmx/incidents/_incident_ticket.html"),
    IncidentTableColumn("links", "Actions", "htmx/incidents/_incident_actions.html"),
]
BUILTIN_COLUMNS = {col.name: col for col in _BUILTIN_COLUMN_LIST}


def get_incident_table_columns() -> List[IncidentTableColumn]:
    columns = getattr(settings, "INCIDENT_TABLE_COLUMNS", argus_htmx_settings.INCIDENT_TABLE_COLUMNS)
    return [_resolve_column(col) for col in columns]


def _resolve_column(col: Union[str, IncidentTableColumn]):
    if isinstance(col, str):
        try:
            col = BUILTIN_COLUMNS[col]
        except KeyError:
            raise ValueError(f"Column '{col}' is not defined")
    return col
