Notifications and notification plugins
--------------------------------------

A notification plugin is a class that inherits from
``argus.notificationprofile.media.base.NotificationMedium``. It has a
``send(event, destinations, **kwargs)`` static method that does the actual
sending.

Email-destinations contain an ``email_address`` and SMS-destinations
contain a ``phone_number``, which is a string that includes the
international calling code, see for instance `Wikipedia: List of
mobile telephone prefixes by country <https://en.wikipedia.org/wiki/List_of_mobile_telephone_prefixes_by_country>`__.
