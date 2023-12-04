.. _ticket-systems:

==============
Ticket systems
==============

It is possible to automatically create a ticket from an Argus incident with
a pre-filled title and body.

How to write a plugin for a desired ticket system is detailed in
:ref:`writing-ticket-system-plugins`.

.. _ticket-systems-settings:

Configuring a ticket plugin
===========================
To enable this feature information needs to be added to the
:ref:`site-specific-settings`.

The settings which are relevant for the integration with the different ticket
systems are ``TICKET_PLUGIN``, ``TICKET_ENDPOINT``,
``TICKET_AUTHENTICATION_SECRET`` and ``TICKET_INFORMATION``.

``TICKET_PLUGIN`` is the fully qualified name of the ticket plugin Python
class.

``TICKET_ENDPOINT`` is the link to the ticket system website the ticket should be
created at.

``TICKET_AUTHENTICATION_SECRET`` is a dictionary containing all the relevant
information that is needed to authenticate with the ticket system's API. It is
both possible to use token-based authentication as well as username- and
password-based authentication.

``TICKET_INFORMATION`` contains any additional information that is needed to
create a ticket, for example the specific repository or queue the ticket should
be created in and settings for custom fields.

To enable an integration with a ticket plugin these settings MUST be added
to Argus.

The specifics for each ticket system plugin is the documentation of the
specific plugin.

Known ticket system plugins
===========================

1st party ticket plugins
------------------------

* Request Tracker: https://pypi.org/project/argus-ticket-rt/, pip install argus-ticket-rt
* Jira: https://pypi.org/project/argus-ticket-jira/, pip install argus-ticket-jira
* Github: https://github.com/Uninett/argus_ticket_github, pip install argus-ticket-github
* Gitlab: https://github.com/Uninett/argus_ticket_gitlab, pip install argus-ticket-gitlab

Other ticket plugins
--------------------

* None known to us at this time

Open an issue to have a plugin added to this list. It needs to be publicly
accessible (and preferably available on PyPI) so we can check the code. We will link up both the
source code repo (or homepage otherwise) and the PyPI-entry.

Writing your own ticket system plugin
=====================================

.. toctree::
   writing-ticket-system-plugins
