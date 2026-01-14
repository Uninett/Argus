==================================================
How to make a column for an ack with a known group
==================================================

You need a new template for the cell, for instance containing::

    {% load argus_htmx %}
    {% if incident|is_acked_by:column.context.group %}X{% endif %}

Our recommended filename for the template file is::

    ``htmx/incident/cells/_incident_ack_by_group.html``

It is *necessary* to use a specialized settings-file for this, since you
need to both set where to look for the additional template, and to set
up the actual column.

Tell Argus where the template is
================================

There are two available methods to tell Argus where the template is. They can
be combined, but then the template in the hardcoded directory name (option 2)
always takes precedence.

1. Add a Django app at the start of :setting:`INSTALLED_APPS` that has
   a directory ``templates/`` that contains the new template file. You can use
   the same app for any other overrides.
2. Add a directory to the :setting:`DIRS` list in the :setting:`TEMPLATES`
   setting, see `Django settings: TEMPLATES
   <https://docs.djangoproject.com/en/5.2/ref/settings/#templates>`_ in the
   official Django documentation. Templates here will override any template
   from any app, provided the relative path matches.

Set up the column
=================

You need to add the column to a column config::

    INCIDENT_TABLE_COLUMN_LAYOUTS = {
        "mylayout":[
            ..
            IncidentTableColumn(
                "mygroup_ack",
                "MYGROUP",
                "htmx/incident/cells/_incident_ack_by_group.html",
                context={"group": "MYGROUP"},
            )
            ..
        ],
        ..
    }
