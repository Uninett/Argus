# customize the displayed columns in the incident table
# items in INCIDENT_TABLE_COLUMNS can be either a `str` referring to a key in
# argus_htmx.incidents.customization.BUILTIN_COLUMNS or an instance of
# argus_htmx.incidents.customization.IncidentTableColumn
INCIDENT_TABLE_COLUMNS = [
    "row_select",
    "id",
    "start_time",
    "status",
    "level",
    "source",
    "description",
    "ack",
    "links",
]
