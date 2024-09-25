.. index::
   integration; destination
   integration; notification plugin

===========================================
Notification plugins: sending notifications
===========================================

Notifications are sent with the help of a notification plugin to one or more
destinations.

A :index:`notification plugin` is a class that inherits from
``argus.notificationprofile.media.base.NotificationMedium``. It has a
``send(event, destinations, **kwargs)`` static method that does the actual
sending.

A :index:`destination` is a user-specific and plugin-specific instance of the
model DestinationConfig. In the DestinationConfig there's a field ``settings``
that has the necessary configuration for where to send the notification for
that type of plugin, like an email address, a phone number or a webhook.

A specific type of destination might also need extra settings in the Django
settings file, this is documented for each plugin.

Existing notification plugins
=============================

1st party, included on install
------------------------------

.. toctree::
   email-plugin
   sms-plugin

1st party, other
----------------

Microsoft Teams
~~~~~~~~~~~~~~~

| Class: argus_notification_msteams.MSTeamsNotification
| Source: https://github.com/Uninett/argus_notification_msteams
| Pypi: `argus-notification-msteams <https://pypi.org/project/argus-notification-msteams/>`_

Other notification plugins
--------------------------

None known to us at this time.

.. note::
   Open an issue (`Github <https://github.com/Uninett/Argus/issues>`_) to have
   a plugin added to this list. It needs to be publicly accessible so we can
   check the code, and be on PyPI. We will link up both the source code repo
   (or homepage otherwise) and the PyPI-entry.

Configuring which notification plugins to use
=============================================

In the :ref:`site-specific-settings` file the setting ``MEDIA_PLUGINS`` is
a list of enabled plugins.

The default is::

    MEDIA_PLUGINS = [
        "argus.notificationprofile.media.email.EmailNotification",
    ]


Writing your own notification plugins
=====================================

.. toctree::
   writing-notification-plugins
