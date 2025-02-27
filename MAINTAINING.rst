=================
Maintenance tasks
=================

Publishing docs
===============

Our docs (Sphinx, restructuredtext, located in `/docs <./docs>`_) are published
at `Read the Docs <https://about.readthedocs.com/>`_, see the `Argus
documentation (online) <https://argus-server.readthedocs.io/en/latest/>`_. This
is automatically handled by GitHub actions.

Occasionally it might be necessary to update the config file, which is
`.readthedocs.yaml <./.readthedocs.yaml>`_. See configuration file options at
`Read the Docs <https://docs.readthedocs.com/platform/stable/config-file/v2.html>`_.

Making new releases
===================

* `Argus release checklist (local copy) <./docs/development/howtos/release-checklist.rst>`_
* `Argus release checklist on rtd <https://argus-server.readthedocs.io/en/latest/development/howtos/release-checklist.html>`_

Note that the final step (making a GitHub release) is needed for the automation
to work correctly in some other repos, notably `argus-docker
<https://github.com/Uninett/argus-docker>`_.


Access to the PyPI project, for publishing releases or other things
-------------------------------------------------------------------

Don't call us, we'll call you.
