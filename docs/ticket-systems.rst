.. _ticket-systems:

==============
Ticket systems
==============

.. toctree::
   ticket-systems/settings
   ticket-systems/writing-ticket-system-plugins

It is possible to automatically create a ticket from an Argus incident with
a pre-filled title and body.

There currently exist plugins for Argus to support ticket creation in
`Request Tracker <https://pypi.org/project/argus-ticket-rt/>`_ and
`Jira <https://pypi.org/project/argus-ticket-jira/>`_.

How to write a plugin for a desired ticket system is detailed in
:ref:`writing-ticket-system-plugins`.

To enable this feature information needs to be added to the
:ref:`site-specific-settings`. How to do that for each ticket system plugin is
detailed in :ref:`ticket-systems-settings` and the documentation of the
specific plugin.
