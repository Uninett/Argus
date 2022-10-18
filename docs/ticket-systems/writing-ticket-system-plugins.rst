.. _writing-ticket-system-plugins:

Writing your own ticket system plugin
=====================================

To write your own ticket system plugin it is easiest to use a Python library
that accesses the API offered by the desired ticket system.

The plugin class inherits from the class ``TicketPlugin`` and needs to implement
the following methods:

.. autoclass:: argus.incident.ticket.base.TicketPlugin
   :members:

Your implementation of ``create_ticket`` should fetch the ticket plugin settings
using ``import_settings``.  Following that, it should use ``create_client`` to
fetch an object through which it can communicate with the ticket system
API.  Using these, it should create a ticket within the ticket system and return
a URL that represents the ticket system's display page for that ticket.  This
method is called within Argus when a user wants to create a ticket.
