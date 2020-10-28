Notifications and notification plugins
--------------------------------------

A notification plugin is a class that inherits from
``argus.notificationprofile.media.base.NotificationMedium``. It has a
``send(incident, user, **kwargs)`` static method that does the actual
sending.

The included ``argus.notificationprofile.media.email.EmailNotification``
needs only ``incident`` and ``user``, while an SMS medium in addition
needs a ``phone_number``. A ``phone_number`` is a string that includes
the international calling code, see for instance `Wikipedia: List of
mobile telephone prefixes by
country <https://en.wikipedia.org/wiki/List_of_mobile_telephone_prefixes_by_country>`__.
