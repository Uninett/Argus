.. _ticket-systems:

==========================
Tickets and ticket systems
==========================

An incident may have a link to a ticket about that incident.

Altering the link to a ticket
=============================

There are two ways to add the link:

1. Create the ticket manually, then store it on the incident
------------------------------------------------------------

A ticket url can be included when creating the incident via POST to the endpoint ``/api/v1/incidents/``.

It can be replaced via PUT or PATCH to ``/api/v1/incidents/{id}/``.

There's also PUTting directly to ``/api/v1/incidents/{id}/ticket_url/``.

Pushing an empty string will unset the ticket link.

2. Use a plugin to create a ticket automatically
------------------------------------------------

PUTing nothing to the API endpoint
``/api/v2/incidents/{incident_pk}/automatic-ticket/}`` will use the configured
ticket system plugin to create a ticket in the configured ticket system. The
resulting new URL is then automatically stored on the incident. To edit,
replace or remove this link, the endpoints in the previous section must be
used.

To enable this feature information needs to be added to the
:ref:`site-specific-settings`. How to do that for each ticket system plugin is
detailed in :ref:`ticket-systems-settings`.

Known ticket system plugins
---------------------------

Open an issue to have a plugin added to this list. It needs to be publicly
accessible so we can check the code, and be on PyPI. We will link up both the
source code repo and the PyPI-entry.

.. toctree::
   ticket-systems/settings
   ticket-systems/writing-ticket-system-plugins
