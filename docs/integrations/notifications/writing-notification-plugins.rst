.. _writing-notification-plugins:

Writing your own notification plugin
====================================

When writing a new notification plugin the plugins for
`SMS-as-Email <https://github.com/Uninett/Argus/blob/main/src/argus/notificationprofile/media/sms_as_email.py>`_
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

You need to set the constants ``MEDIA_SLUG``, ``MEDIA_NAME`` and
``MEDIA_JSON_SCHEMA``. If your plugin only takes or needs a single
configuration flag you should also set ``MEDIA_SETTINGS_KEY``.

MEDIA_NAME
   The media name is the name of the service you want to send notifications by.
   This is used only for display purposes so you might want to keep it short
   and sweet. So for example ``"Email"``, ``"SMS"`` or ``"MS Teams"``.

MEDIA_SLUG
   The media slug is the slugified version of that, so the name simplified to
   only contain lowercase letters, numbers, underscores and hyphens. Always
   have it start with a letter, a-z. For example ``"email"``, ``"sms"`` or
   ``"msteams"``.

MEDIA_JSON_SCHEMA
   The media `json schema <https://json-schema.org/>`_ is a representation of
   how a destination that will be used by this notification plugin should look
   like, so that it is possible to autogenerate a form with JavaScript. It will
   be accessible via the API. Such a destination should include all necessary
   information that is needed to send notifications with your notification
   plugin. In case of SMS that is a phone number or for MS Teams a webhook.

MEDIA_SETTINGS_KEY
   The media settings key is the name of the most important key in the settings
   JSON field. It is used to cut down on the amount of code you need to write
   if there is only one piece of config you need to send the notification.
   Among other things, it is used to check for duplicate entries, so in a way
   it acts as storage for the value of the primary key for a destination plugin. For that reason, it must be
   required in the json schema. For example for an email plugin this would be
   "email_address" or for a SMS plugin it would be "phone_number".

Form
   The ``forms.Form`` used to validate the settings-field.

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

Helper class methods
--------------------

.. autoclass:: argus.notificationprofile.media.base.NotificationMedium
   :members: get_label, has_duplicate, raise_if_not_deletable, update, validate
   :noindex:

With a little luck you might not need to override any of these.

get_label
   Your implementation of ``get_label`` should show a reasonable representation
   for a destination of that type that makes it easy to identify. For SMS that
   would simply be the phone number. The default implementation uses
   ``MEDIA_SETTINGS_KEY`` to look up the most important piece of information in
   the settings and uses that directly.
   If the label would be very long, for instance if the needed setting is a
   very long url (40+ characters), you should write your own ``get_label``.

has_duplicate
   The method ``has_duplicate`` will receive a QuerySet of destinations and
   a dict of settings for a possible destination and should return True if
   a destination with such settings exists in the given QuerySet. By default it
   will use ``MEDIA_SETTINGS_KEY`` to lookup the most important piece of
   information in the settings.

get_relevant_address
   Used by ``send``. You should only need to override this if the key in
   MEDIA_SETTINGS_KEY is insuffcient to look up the actual configuration of the
   destinations of the type set by MEDIA_SLUG.

validate
   The function ``validate`` makes sure that a destination with the given
   medium, label and settings can be updated or created. It uses the
   ``validate_settings`` method to validate the settings-field, a form
   (CommonDestinationConfigForm) to validate the media and label-fields, and an
   optional DestinationConfig instance for checking that readonly values were
   not changed and that no duplicates are created. The validated form is
   returned if ok, otherwise a ``ValidationError`` should be raised. It is
   unlikely that you will ever need to override this method.

validate_settings
   This method validates the actual contents of the settings-field using the
   ``Form`` that is defined and an optional DestinationConfig instance for
   the function ``has_duplicate`` that can be used here to ensure that no two
   destinations with the same settings will be created. A ``ValidationError``
   should be raised  if the given settings are invalid, and the validated and
   cleaned data should be returned if not.

raise_if_not_deletable
   This method by default checks if the destination is in use by a profile, or
   if it is **managed**, that is, outside of the control of a user. It should
   raise ``NotDeletableError`` in either case. If the destination *may* be
   deleted it should return ``None``. It should not be necessary to alter or
   extend this method, but if it is, ``super()`` should be used to maintain the
   standard functionality.

update
   This method only has to be implemented if the regular update method is
   insufficient. This can be the case if there is more than one key-value pair
   in settings that need to be updated.

Writing destination plugins using Apprise
-----------------------------------------
`Apprise <https://pypi.org/project/apprise/>`_ is an **optional dependency** — install it with::

    pip install argus-server[apprise]

If one wishes to write a notification plugin for a medium supported by Apprise, see `Apprise documentation: Supported services
<https://appriseit.com/services/>`__, a pre-made base class is provided that allows you to get started almost straight "out of the box".

| Class: ``argus.notificationprofile.media.base.AppriseMedium``

A minimal example of how to use it can be found in:

| Class: ``argus.notificationprofile.media.slack.SlackNotification``

In this case as Apprise works with URLs, it can consume the destination webhook directly, so the notification class does not actually need anything.

Nevertheless, it is probably smart to set the constants to be less generic and provide an extension of the ``validate`` function using your desired `MEDIA_SLUG`.

Note that if you change the name of the core ``destination_url`` property, you will need to extend many more of the functions to use the new name.

The default ``destination_url`` field implementation only supports http / https URLs.
To use custom schemes (like the generic `service://configuration/?parameters` in the `Apprise docs <https://appriseit.com/getting-started/universal-syntax/>`_),
you need to create a custom subclass overriding the appropriate fields and functions.
