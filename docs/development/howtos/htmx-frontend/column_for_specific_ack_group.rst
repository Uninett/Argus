==================================================
How to make a column for an ack with a known group
==================================================

You need a template for the cell, in ``src/argus/htmx/templates/htmx/incidents/_incident_ack_by_group.html``::

    {% load argus_htmx %}
    {% if incident|is_acked_by:column.context.group %}X{% endif %}

You also need to add the column to the column config::

    INCIDENT_TABLE_COLUMNS = [
        ..
        IncidentTableColumn(
            "mygroup_ack",
            "MYGROUP",
            "htmx/incidents/_incident_ack_by_group.html",
            context={"group": "MYGROUP"},
        )
        ..
    ]
