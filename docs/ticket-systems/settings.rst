.. _ticket-systems-settings:

Settings for integration with ticket systems
============================================

The settings which are relevant for the integration with the different ticket
systems are ``TICKET_PLUGIN``, ``TICKET_ENDPOINT``,
``TICKET_AUTHENTICATION_SECRET`` and ``TICKET_INFORMATION``.

``TICKET_PLUGIN`` is the fully qualified name of the ticket plugin Python
class. The included plugins are located in the ``argus.incident.ticket``
namespace, so the path should look something like this:
``argus.incident.ticket.FileName.PluginName``.

``TICKET_ENDPOINT`` is the link to the ticket system website the ticket should be
created at.

``TICKET_AUTHENTICATION_SECRET`` is a dictionary containing all the relevant
information that is needed to authenticate with the ticket system's API. It is
both possible to use token-based authentication as well as username- and
password-based authentication.

``TICKET_INFORMATION`` contains any additional information that is needed to
create a ticket, for example the specific repository or queue the ticket should
be created in.

To enable an integration with a ticket plugin these settings MUST be added
to Argus.

Jira
----

* ``TICKET_PLUGIN``: ``"argus.incident.ticket.jira.JiraPlugin"``
* ``TICKET_ENDPOINT``: ``"https://jira.atlassian.net"`` or link to cloud- or self-hosted instance
* ``TICKET_AUTHENTICATION_SECRET``:
    - create an `API token <https://id.atlassian.com/manage-profile/security/api-tokens>`_
    - add it like this: ``{"token": API token}``
    - if you're using a cloud-hosted instance, also add your email address like this: ``{"token": API token, "email": email address}``
* ``TICKET_INFORMATION``:
    - to know which project to create the ticket in the Jira API needs to know the project key or id of it
    - to figure out the project key visit the section Project Key of the `Jira ticket documentation <https://support.atlassian.com/jira-software-cloud/docs/what-is-an-issue/>`_
    - to figure out the project id visit this `guide on how to get the project id <https://confluence.atlassian.com/jirakb/how-to-get-project-id-from-the-jira-user-interface-827341414.html/>`_
    - fill the dictionary like this: ``{"project_key_or_id": project key/id}``
    - in case the tickets should have a different type than ``Task``, add it to the dictionary like this: ``{"project_key_or_id": project key/id, "type": "Epic"|"Story"|"Task"|"Bug"|"Subtask"|any other ticket type}``