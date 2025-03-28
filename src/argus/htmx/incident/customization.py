"""
Definitions and defaults for UI customization on the incidents page.

Currently customizable UI elements:
- table columns: configure what columns to show in the incidents listing
"""

from dataclasses import dataclass
from typing import Optional, Union

from django.conf import settings

from argus.htmx import defaults as argus_htmx_settings

# for editor typeahead
CELL_WRAPPER_TEMPLATE_DEFAULT = "htmx/incident/_incident_table_cell_wrapper_default.html"
CELL_WRAPPER_TEMPLATE_LINK_TO_DETAILS = "htmx/incident/_incident_table_cell_wrapper_link_to_details.html"


@dataclass
class IncidentTableColumn:
    """Class for defining a column in the incidents table.

    :param name: identifier for this column
    :param label: what to show as the column header
    :param cell_template: template to use when rendering a cell for this column
    :param context: additional context to pass to the rendering cell. Will be made
        available as ``cell_context`` in the cell template
    :param filter_field: when given, this column is considered filterable and a filter
        input is attached to the column header that can provide a query param with `filter_field`
        as the key
    """

    name: str  # identifier
    label: str  # display value
    cell_template: str
    header_template: Optional[str] = None
    context: Optional[dict] = None
    filter_field: Optional[str] = None
    cell_wrapper_template: str = CELL_WRAPPER_TEMPLATE_DEFAULT
    column_classes: str = ""


_BUILTIN_COLUMN_LIST = [
    IncidentTableColumn(
        "color_status",
        "",
        "",
        cell_wrapper_template="htmx/incident/cells/_incident_color_status.html",
        column_classes="w-4 p-0",
    ),
    IncidentTableColumn(
        "row_select",
        "Selected",
        "htmx/incident/cells/_incident_checkbox.html",
        header_template="htmx/incident/cells/_incident_list_select_all_checkbox_header.html",
    ),
    IncidentTableColumn(
        "id",
        "ID",
        "htmx/incident/cells/_incident_pk.html",
        cell_wrapper_template=CELL_WRAPPER_TEMPLATE_LINK_TO_DETAILS,
    ),
    IncidentTableColumn(
        "start_time",
        "Timestamp",
        "htmx/incident/cells/_incident_start_time.html",
        header_template="htmx/incident/cells/_incident_start_time_header.html",
        cell_wrapper_template=CELL_WRAPPER_TEMPLATE_LINK_TO_DETAILS,
    ),
    IncidentTableColumn("status", "Status", "htmx/incident/cells/_incident_status.html"),
    IncidentTableColumn(
        "level",
        "Severity level",
        "htmx/incident/cells/_incident_level.html",
        cell_wrapper_template=CELL_WRAPPER_TEMPLATE_LINK_TO_DETAILS,
    ),
    IncidentTableColumn(
        "source",
        "Source",
        "htmx/incident/cells/_incident_source.html",
        cell_wrapper_template=CELL_WRAPPER_TEMPLATE_LINK_TO_DETAILS,
    ),
    IncidentTableColumn(
        "description",
        "Description",
        "htmx/incident/cells/_incident_description.html",
        cell_wrapper_template=CELL_WRAPPER_TEMPLATE_LINK_TO_DETAILS,
    ),
    IncidentTableColumn("ack", "Ack", "htmx/incident/cells/_incident_ack.html"),
    IncidentTableColumn(
        "combined_status",
        "Status",
        "htmx/incident/cells/_incident_combined_status.html",
        cell_wrapper_template=CELL_WRAPPER_TEMPLATE_LINK_TO_DETAILS,
    ),
    IncidentTableColumn(
        "ticket",
        "Ticket",
        "htmx/incident/cells/_incident_ticket.html",
    ),
    IncidentTableColumn(
        "links",
        "Actions",
        "htmx/incident/cells/_incident_actions.html",
    ),
]
BUILTIN_COLUMNS = {col.name: col for col in _BUILTIN_COLUMN_LIST}


def get_incident_table_columns() -> list[IncidentTableColumn]:
    columns = getattr(settings, "INCIDENT_TABLE_COLUMNS", argus_htmx_settings.INCIDENT_TABLE_COLUMNS)
    return [_resolve_column(col) for col in columns]


def _resolve_column(col: Union[str, IncidentTableColumn]):
    if isinstance(col, str):
        try:
            col = BUILTIN_COLUMNS[col]
        except KeyError:
            raise ValueError(f"Column '{col}' is not defined")
    return col
