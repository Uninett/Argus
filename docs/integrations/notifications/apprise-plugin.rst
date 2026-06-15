Apprise notifications using minimal approach
============================================

| Class: ``argus.notificationprofile.media.base.AppriseMedium``

This plugin is **not** enabled by default.

This is the base plugin for using `Apprise <https://appriseit.com/>`_ to send notifications. Apprise is a 3rd party library that wraps the APIs of more than a hundred notification services.
Apprise is not installed automatically, you can install it with::

    pip install argus-server[apprise]

The settings-field for an apprise-destination contains an Apprise destination URL for a supported medium,
examples of which can be found here:`Apprise documentation: Supported services
<https://appriseit.com/services/>`_. Regular webhooks can also be used directly.
