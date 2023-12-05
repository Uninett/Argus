argus.notificationprofile.media.sms_as_email.SMSNotification
============================================================

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
