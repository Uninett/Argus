=======================================
How to make a column for a specific tag
=======================================

You only need to add the column to the column config::

    INCIDENT_TABLE_COLUMNS = [
        ..
        IncidentTableColumn(
            "mytag",
            "MYTAG",
            "htmx/incidents/cells/_incident_tag.html",
            context={"tag": "MYTAG"},
        )
        ..
    ]
