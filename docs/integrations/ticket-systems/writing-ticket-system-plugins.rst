.. _writing-ticket-system-plugins:

Writing your own ticket system plugin
=====================================

To create a project for a new plugin easily it is recommended to use the
`Argus Ticket Cookiecutter Template <https://github.com/Uninett/argus_ticket_cookiecutter>_`.

To write your own ticket system plugin it is easiest to use a Python library
that accesses the API offered by the desired ticket system.

The plugin class inherits from the class ``TicketPlugin`` and needs to implement
the following methods:

.. autoclass:: argus.incident.ticket.base.TicketPlugin
   :members:

Your implementation of ``create_ticket`` should fetch the ticket plugin
settings. For that you can simply use the inherited method ``import_settings``,
override or expand it.

Following that, ``create_client`` should be used to fetch an object through
which it can communicate with the ticket system's API.

Then you can call the function ``create_html_body`` that is also inherited from
``TicketPlugin`` to create an html body using the serialized incident that
``create_ticket`` gets as a parameter. This function uses the template
``default_ticket_body.html`` to create an html body for a ticket. You can also
override this function to use your own template.

Using the imported settings, the client and potentially the html body, a ticket
should be created in the ticket system and the URL for that ticket's display
page should be returned.

The method ``create_ticket`` is called within Argus when a user wants to create
a ticket.
