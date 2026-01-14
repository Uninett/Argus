=======================================
How to make a column for a specific tag
=======================================

You can add the column to a named column config::

    INCIDENT_TABLE_COLUMN_LAYOUTS = {
        "mylayout": [
            ..
            IncidentTableColumn(
                "mytag",
                "MYTAG",
                "htmx/incidents/cells/_incident_tag.html",
                context={"tag": "MYTAG"},
            )
            ..
        ]
        ..
    }
