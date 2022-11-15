------------------------------------
Notifications and their destinations
------------------------------------

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

Notification plugins included on install
----------------------------------------

argus.notificationprofile.media.email.EmailNotification
.......................................................

This plugin is enabled by default.

This plugin uses the email server settings provided by Django itself to
configure the server.

The settings-field for an email-destination contains an
``email_address``-field. It also contains a read-only ``synced``-field, which
is used for some magic if the User model-instance has its
``email_address``-field set. If the email-address has ``synced`` set to True, that
email-address is read-only as far as the API is concerned, because the address
on the User is synced to that specific destination.

To validate the email address we use Django's own email validator.

argus.notificationprofile.media.sms_as_email.SMSNotification
............................................................

This plugin is **not** enabled by default.

This plugin is for systems where SMSes are sent via a magical email-address
(legacy-system support). For that reason it depends on the same Django email
server settings as the included EmailNotification-plugin, and in addition the
Argus-specific ``SMS_GATEWAY_ADDRESS``-setting, which is the magical
email-address to send the SMSes to.

The phone number is suffixed to the local-part of the email-address.

Given an ``SMS_GATEWAY_ADDRESS`` of the following form::

    SMS_GATEWAY_ADDRESS = "sms@example.com"

and a phone number of the following form::

    +345656787643

then the resulting address is::

    sms+345656787643@example.com

The settings-field for an SMS-destination contains only a ``phone_number``,
which is a string that includes the international calling code, see for
instance `Wikipedia: List of mobile telephone prefixes by country
<https://en.wikipedia.org/wiki/List_of_mobile_telephone_prefixes_by_country>`__.

The library used to validate that the number is a real phone number is based on
`Google's libphonenumber <https://github.com/google/libphonenumber>`_, so you
cannot test with an arbitrary string of numbers.

This plugin is a better example to copy for your own plugins than the included
email-plugin since it doesn't have the Django-specific User-magic.

Other notification plugins
--------------------------

Open an issue to have a plugin added to this list. It needs to be publicly
accessible so we can check the code, and be on PyPI. We will link up both the
source code repo and the PyPI-entry.

Writing your own notification plugins
-------------------------------------

TBD
