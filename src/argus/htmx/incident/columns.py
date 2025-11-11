"""
Definitions and defaults for UI customization on the incidents page.

Currently customizable UI elements:
- table columns: configure what columns to show in the incidents listing
"""

import logging
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

from argus.htmx.defaults import INCIDENT_TABLE_COLUMNS as BUILTIN_INCIDENT_TABLE_COLUMNS


LOG = logging.getLogger(__name__)

# for editor typeahead
CELL_WRAPPER_TEMPLATE_DEFAULT = "htmx/incident/_incident_table_cell_wrapper_default.html"
CELL_WRAPPER_TEMPLATE_LINK_TO_DETAILS = "htmx/incident/_incident_table_cell_wrapper_link_to_details.html"

_BUILTIN_COLUMN_LAYOUT_NAME = "built-in"
_DEFAULT_COLUMN_LAYOUT_NAME = "default"


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

    name: str  # unique identifier
    label: str  # display value
    cell_template: str
    header_template: Optional[str] = None
    context: Optional[dict] = None
    filter_field: Optional[str] = None
    detail_link: bool = False
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
        detail_link=True,
    ),
    IncidentTableColumn(
        "start_time",
        "Timestamp",
        "htmx/incident/cells/_incident_start_time.html",
        header_template="htmx/incident/cells/_incident_start_time_header.html",
        detail_link=True,
    ),
    IncidentTableColumn(
        "status",
        "Status",
        "htmx/incident/cells/_incident_status.html",
        detail_link=True,
    ),
    IncidentTableColumn(
        "level",
        "Severity level",
        "htmx/incident/cells/_incident_level.html",
        detail_link=True,
    ),
    IncidentTableColumn(
        "select_levels",
        "Severity level",
        "htmx/incident/cells/_incident_level.html",
        detail_link=True,
        filter_field="level",
    ),
    IncidentTableColumn(
        "source",
        "Source",
        "htmx/incident/cells/_incident_source.html",
        detail_link=True,
    ),
    IncidentTableColumn(
        "description",
        "Description",
        "htmx/incident/cells/_incident_description.html",
        detail_link=True,
    ),
    IncidentTableColumn(
        "search_description",
        "Description",
        "htmx/incident/cells/_incident_description.html",
        detail_link=True,
        filter_field="description",
    ),
    IncidentTableColumn(
        "ack",
        "Ack",
        "htmx/incident/cells/_incident_ack.html",
        detail_link=True,
    ),
    IncidentTableColumn(
        "combined_status",
        "Status",
        "htmx/incident/cells/_incident_combined_status.html",
        detail_link=True,
    ),
    IncidentTableColumn(
        "ticket",
        "Ticket",
        "htmx/incident/cells/_incident_ticket.html",
    ),
    IncidentTableColumn(
        "has_ticket_url",
        "Ticket",
        "htmx/incident/cells/_incident_ticket.html",
        filter_field="has_ticket",
    ),
    IncidentTableColumn(
        "search_ticket_url",
        "Ticket",
        "htmx/incident/cells/_incident_ticket.html",
        filter_field="ticket_url",
    ),
    IncidentTableColumn(
        "links",
        "Actions",
        "htmx/incident/cells/_incident_actions.html",
    ),
]
BUILTIN_COLUMNS = {col.name: col for col in _BUILTIN_COLUMN_LIST}


def get_builtin_column_layout():
    return _BUILTIN_COLUMN_LAYOUT_NAME, BUILTIN_INCIDENT_TABLE_COLUMNS


def get_default_column_layout():
    column_setting = getattr(settings, "INCIDENT_TABLE_COLUMNS", [])
    LOG.debug("Getting INCIDENT_TABLE_COLUMNS: column_setting: %s", column_setting)
    return _DEFAULT_COLUMN_LAYOUT_NAME, column_setting


def get_available_column_layouts():
    builtin, builtin_columns = get_builtin_column_layout()
    layouts = {builtin: builtin_columns}

    default, default_columns = get_default_column_layout()
    if default_columns:
        layouts[default] = default_columns
    LOG.debug("Available column layouts: %s", layouts)
    return layouts


def get_column_choices():
    _columns = get_available_column_layouts().keys()
    columns = [(column_name, column_name.title()) for column_name in _columns]
    return columns


def get_incident_table_columns(name: str = _BUILTIN_COLUMN_LAYOUT_NAME) -> list[IncidentTableColumn]:
    LOG.debug("Getting layouts: get_incident_table_columns")
    layouts = get_available_column_layouts()
    if name not in layouts:
        name = _BUILTIN_COLUMN_LAYOUT_NAME
    columns = layouts[name]
    return [_resolve_column(col) for col in columns]


def get_default_column_layout_name():
    LOG.debug("Getting layouts: get_default_column_layout_name")
    layouts = get_available_column_layouts()
    if _DEFAULT_COLUMN_LAYOUT_NAME in layouts.keys():
        return _DEFAULT_COLUMN_LAYOUT_NAME
    return _BUILTIN_COLUMN_LAYOUT_NAME


def _resolve_column(col: str | IncidentTableColumn):
    if isinstance(col, str):
        try:
            col = BUILTIN_COLUMNS[col]
        except KeyError:
            raise ValueError(f"Column '{col}' is not defined")
    return col
