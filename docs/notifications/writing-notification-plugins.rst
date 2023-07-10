.. _writing-notification-plugins:

Writing your own notification plugin
====================================

When writing a new notification plugin the plugins for
`SMS-as-Email <https://github.com/Uninett/Argus/blob/master/src/argus/notificationprofile/media/sms_as_email.py>`_
and
`Teams <https://github.com/Uninett/argus_notification_msteams/blob/main/src/argus_notification_msteams.py>`_
can be used as guides.

To create a project for a new plugin easily it is recommended to use the
`Argus Notification Cookiecutter Template <https://github.com/Uninett/argus-notification-cookiecutter>`_.

If a Python library that speaks the protocol of the medium already exists, we
recommend that you use it. This helps keep the plugin itself short and simple.
Just remember to add the library as a dependency in the ``pyproject.toml``.

.. note:: Do not forget to add the path to your new notification plugin to the
         setting :setting:`MEDIA_PLUGINS` to be able to use it.

         Also let us know about your notification plugin so that we can link
         your notification plugin and can add it to the frontend.

The plugin class inherits from the class ``NotificationMedium`` and needs to
implement the following:

Class constants
---------------

You need to set the constants `MEDIA_SLUG`, `MEDIA_NAME` and
`MEDIA_JSON_SCHEMA`.

The media name is the name of the service you want to send notifications by.
This is used only for display purposes so you might want to keep it short and
sweet. So for example `Email`, `SMS` or `MS Teams`.

The media slug is the slugified version of that, so the name simplified to only
contain lowercase letters, numbers, underscores and hyphens. Always have it
start with a letter, a-z. For example `email`, `sms` or `msteams`.

The media `json schema <https://json-schema.org/>`_ is a representation of how
a destination that will be used by this notification plugin should look like.
Such a destination should include all necessary information that is needed to
send notifications with your notification plugin. In case of SMS that is a
phone number or for MS Teams a webhook.

Class methods for sending notifications
---------------------------------------

.. autoclass:: argus.notificationprofile.media.base.NotificationMedium
   :members: send

The ``send`` method is the method that does the actual sending of the
notification. It gets the Argus event and a list of destinations as input and
returns a boolean indicating if the sending was successful.

It is recommended to first filter the given QuerySet of destinations to only
include destinations of the appropriate medium.

The rest is very dependent on the notification medium and, if used, the Python
library. The given event can be used to extract relevant information that
should be included in the message that will be sent to each destination.

Class methods for destinations
------------------------------

.. autoclass:: argus.notificationprofile.media.base.NotificationMedium
   :members: get_label, has_duplicate, raise_if_not_deletable, update, validate
   :noindex:

Your implementation of ``get_label`` should show a reasonable representation
for a destination of that type that makes it easy to identify. For SMS that
would simply be the phone number.

The method ``has_duplicate`` will receive a QuerySet of destinations and a dict
of settings for a possible destination and should return True if a destination
with such settings exists in the given QuerySet.

``raise_if_not_deletable`` should check if a given destination can be deleted.
This is used in case some destinations are synced from an outside source and
should not be able to be deleted by a user. If that is the case a
``NotDeletableError`` should be raised. If not simply return None.

The method ``update`` only has to be implemented if the regular update method
of Django isn't sufficient. This can be the case if additional settings need to
be updated.

Finally the function ``validate`` makes sure that a destination with the given
settings can be updated or created. The function ``has_duplicate`` can be used
here to ensure that not two destinations with the same settings will be
created. Additionally the settings themselves should also be validated. For
example for SMS the given phone number will be checked. Django forms can be
helpful for validation. A ``ValidationError`` should be raised if the given
settings are invalid and the validated and cleaned data should be returned if
not.
