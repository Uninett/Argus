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

Github
------

* ``TICKET_PLUGIN``: ``"argus.incident.ticket.github.GithubPlugin"``
* ``TICKET_ENDPOINT``: ``"https://github.com/"`` or link to self-hosted instance
* ``TICKET_AUTHENTICATION_SECRET``:
    - create a `personal access token <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token>`_ with the scope "``repo``"
    - add it like this: ``{"token": personal_access_token}``
* ``TICKET_INFORMATION``:
    - to know which project to create the ticket in the Github API needs to know the owner and name of it
    - the owner is the user or organization the Github repository belongs to
    - the name is the name of the Gitlab project
    - fill the dictionary like this: ``{"project_namespace_and_name": owner/name}``
    - for the Github project `Hello Git World <https://github.com/githubtraining/hellogitworld>`_ the dictionary would look like this: ``{"project_namespace_and_name": "githubtraining/hellogitworld"}``
