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

Gitlab
------

* ``TICKET_PLUGIN``: ``"argus.incident.ticket.gitlab.GitlabPlugin"``
* ``TICKET_ENDPOINT``: ``"https://gitlab.com/"`` or link to self-hosted instance
* ``TICKET_AUTHENTICATION_SECRET``:
    - create a `project access token <https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html>`_ or a `personal access token <https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html>`_ with the scope "``api``"
    - add it like this: ``{"token": project/personal access token}``
* ``TICKET_INFORMATION``:
    - to know which project to create the ticket in the Gitlab API needs to know the namespace and name of it
    - to figure out the namespace visit the `namespace page <https://docs.gitlab.com/ee/user/namespace/>`_ of the Gitlab documentation
    - the name is the name of the Gitlab project
    - fill the dictionary like this: ``{"project_namespace_and_name": "namespace/name"}``
    - for the Gitlab project `Simple Maven Example <https://gitlab.com/gitlab-examples/maven/simple-maven-example>`_ the dictionary would look like this: ``{"project_namespace_and_name": "gitlab-examples/maven/simple-maven-example"}``
