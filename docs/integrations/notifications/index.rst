====================================
Notifications and their destinations
====================================

Notifications are sent with the help of notification plugins to destinations.

A notification plugin is a class that inherits from
``argus.notificationprofile.media.base.NotificationMedium``. It has a
``send(event, destinations, **kwargs)`` static method that does the actual
sending.

A destination is a user-specific and plugin-specific instance of the model
DestinationConfig. In the DestinationConfig there's a field ``settings`` that
has the necessary configuration for where to send the notification for that
type of plugin, like an email address, a phone number or a webhook.

A specific type of destination might also need extra settings in the Django
settings file, this is documented for each plugin.

Configuring which notification plugins to use
=============================================

In the :ref:`site-specific-settings` file the setting ``MEDIA_PLUGINS`` is
a list of enabled plugins.

The default is::

    MEDIA_PLUGINS = [
        "argus.notificationprofile.media.email.EmailNotification",
    ]

Notification plugins included on install
========================================

.. toctree::
   email-plugin
   sms-plugin

Other notification plugins
==========================

Open an issue to have a plugin added to this list. It needs to be publicly
accessible so we can check the code, and be on PyPI. We will link up both the
source code repo (or homepage otherwise) and the PyPI-entry.

argus_notification_msteams.MSTeamsNotification
----------------------------------------------

| Source: https://github.com/Uninett/argus_notification_msteams
| PyPI: https://pypi.org/project/argus-notification-msteams/

Writing your own notification plugins
=====================================

.. toctree::
   writing-notification-plugins
