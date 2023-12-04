.. Argus documentation master file, created by
   sphinx-quickstart on Fri Apr 24 09:29:51 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

============
Integrations
============

Argus can integrate with monitoring systems via external glue services. It can
integrate with ticket systems via ticket plugins, and with notification systems
via notification plugins.

In short:

* Monitoring systems send their alerts via a *glue service*. Either via an
  argus-plugin (e.g. nav) or a standalone microservice (e.g. nagios). The
  service is registered in Argus with a source type and a source, which allows
  multiple entries from the same type. The source has a token connected with
  it, which the service uses to authenticate.
* Notification systems are hooked up via plugins. The plugins are installed
  (via pip) to the same environment as Argus. Most plugins are configured solely via
  the web interface, except for the two included email-based plugins. These
  piggyback on the email server configuration of Argus itself (see
  :ref:`site-specific-settings`).
* A single ticket system is hooked up via a plugin. It is installed (via pip)
  to the same path as argus. All ticket system plugins are configured via the
  settings file, see :ref:`site-specific-settings`.

.. toctree::
   glue-services/index
   notifications/index
   ticket-systems/index
   :maxdepth: 2
   :caption: Contents:
