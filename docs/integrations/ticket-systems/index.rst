.. index::
   integration; ticket system plugin
   ticket system plugin

.. _ticket-systems:

======================================================
Ticket system plugins: Creating a ticket automatically
======================================================

.. index::
   see: case; ticket
   see: issue; ticket

It is possible to automatically create a :index:`ticket` (aka. issue, case)
from an Argus incident with a pre-filled title and body.

How to write a plugin for a desired ticket system is detailed in
:ref:`writing-ticket-system-plugins`.

Existing ticket system plugins
==============================

Ticket plugins maintained by Argus developers
---------------------------------------------

Request Tracker
~~~~~~~~~~~~~~~

| Class: ``argus_ticket_rt.RequestTrackerPlugin``
| Source: https://github.com/Uninett/argus_ticket_rt
| PyPI: `argus-ticket-rt <https://pypi.org/project/argus-ticket-rt/>`_

Jira
~~~~

| Class: ``argus_ticket_jira.JiraPlugin``
| Source: https://github.com/Uninett/argus_ticket_jira
| PyPI: `argus-ticket-jira <https://pypi.org/project/argus-ticket-jira/>`_

Github
~~~~~~

| Class: ``argus_ticket_github.GithubPlugin``
| Source: https://github.com/Uninett/argus_ticket_github
| PyPI: `argus-ticket-github <https://pypi.org/project/argus-ticket-github/>`_

Gitlab
~~~~~~

| Class: ``argus_ticket_gitlab.GitlabPlugin``
| Source: https://github.com/Uninett/argus_ticket_gitlab
| PyPI: `argus-ticket-gitlab <https://pypi.org/project/argus-ticket-gitlab/>`_

Other ticket plugins
--------------------

None known to us at this time.

.. include:: ../_note.rst

.. _ticket-systems-settings:

Configuring a ticket plugin
===========================

To enable this feature information needs to be added to the
:ref:`site-specific-settings`.

The settings which are relevant for the integration with the different ticket
systems are ``TICKET_PLUGIN``, ``TICKET_ENDPOINT``,
``TICKET_AUTHENTICATION_SECRET`` and ``TICKET_INFORMATION``.

``TICKET_PLUGIN`` is the fully qualified name of the ticket plugin Python
class. See the "Class" field in the list of plugins above for examples.

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

Writing your own ticket system plugin
=====================================

.. toctree::
   writing-ticket-system-plugins
