=========
Endpoints
=========

Administration endpoint
-----------------------
Use ``/admin/`` to access the project’s admin pages.

Authorization
-------------

All endpoints require requests to contain a header with key
``Authorization`` and value ``Token {token}``, where ``{token}`` is
replaced by a registered auth token. These are generated per user by
logging in through Feide, and can be found at
``/admin/authtoken/token/``.

Auth endpoints
--------------

-  ``GET`` to ``/api/v1/auth/user/``: returns the logged in user

-  ``GET`` to ``/api/v1/auth/users/<int:pk>/``: returns a user by primary key
   (``pk``)

-  ``POST`` to ``/oidc/api-token-auth/``: returns an auth token for the
   posted user

   -  Note that this token will expire after 14 days, and can be
      replaced by posting to the same endpoint.

   .. code-block:: json
    :caption: Example request body

      {
        "username": "alice",
        "password": "secret"
      }

-  ``/oidc/login/dataporten_feide/``: redirects to Feide login

-  ``/api/v1/auth/phone-number/``:

   -  ``GET``: returns the phone numbers of the logged in user

      .. code-block:: json
        :caption: Example response body

          [
            {
              "pk": 2,
              "user": 1,
              "phone_number": "+4767676767"
            },
            {
              "pk": 1,
              "user": 1,
              "phone_number": "+4790909090"
            }
          ]


   -  ``POST``: creates and returns the phone numbers of the logged in
      user

      .. code-block:: json
        :caption: Example request body

          {
            "pk": 2,
            "phone_number": "+4767676767"
          }


-  ``/api/v1/auth/phone-number/<int:pk>/``:

   -  ``GET``: returns the specific phone number of the logged in user

      .. code-block:: json
        :caption: Example response body

          {
            "pk": 2,
            "user": 1,
            "phone_number": "+4767676767"
          }

   -  ``PUT``: updates and returns one of the logged in user’s phone
      numbers by primary key

      -  Example request body: same as ``POST`` to
         ``/api/v1/auth/phone-number/``

   -  ``DELETE``: deletes one of the logged in user’s phone numbers by
      primary key

   .. note::

     The phone number is validated using the python port of
     `libphonenumber <https://github.com/google/libphonenumber>`__. It
     will check that the phone number is in a valid number series. Using a
     random number will not work.


Incident endpoints
------------------

-  ``/api/v1/incidents/``:

   -  ``GET``: returns all incidents - both open and historic

      **Query parameters**: All query parameters are optional. If a query
      parameter is not included or empty, for instance ``acked=``, then
      the rows returned are not affected by that filter and shows rows
      of all kinds of that value, for instance both “acked” and
      “unacked” in the case of ``acked=``.

      **Filtering parameters**:

      ``acked=true|false``
        Fetch only acked (``true``) or unacked (``false``) incidents.

      ``open=true|false``
        Fetch only open (``true``) or closed (``false``) incidents.

      ``stateful=true|false``
        Fetch only stateful (``true``) or stateless (``false``) incidents.

      ``source__id__in=ID1[,ID2,..]``
        Fetch only incidents with a source with numeric id ``ID1`` or ``ID2`` or..

      ``source__name__in=NAME1[,NAME2,..]``
        Fetch only incidents with a source with name ``NAME1`` or ``NAME2`` or..

      ``source_incident_id=ID``
        Fetch only incidents with ``source_incident_id`` set to ``ID``.

      ``ticket``
        Fetch only incidents with a ticket url (``true``) or without (``false``).

      ``tags=key1=value1,key1=value2,key2=value``
        Fetch only incidents with one or more of the tags. Tag-format is
        “``key=value``”. If there are multiple tags with the same key, only
        one of the tags need match. If there are multiple keys, one of
        each keys must match.

      So:

      .. code-block::
        :caption: URL reformatted for readability

          /api/v1/incidents/?acked=false\
                          &open=true\
                          &stateful=true\
                          &source__id__in=1\
                          &tags=\
                            location=broomcloset,\
                            location=understairs,\
                            problem=onfire

      will fetch incidents that are all of “open”, “unacked”,
      “stateful”, from source number 1, with “location” either
      “broomcloset” or “understairs”, and that is on fire.

      .. note::
        If the boolean parameters are not given a value
        or are left out, that is interpreted as not filtering at all on
        that parameter, showing both true and false entries.

      **Paginating parameters**:

      ``cursor=LONG RANDOM STRING|null``
        Go to the page of that cursor. The cursor string for next and
        previous page is part of the response body.

      ``page_size=INTEGER``
        The number of rows to return. Default is 100.

      So:
      ``api/v1/incidents/?cursor=cD0yMDIw&page_size=10``
      will go to the page indicated by
      ``cD0yMDIw`` and
      show the next 10 rows from that point onward. Do not attempt to
      guess the cursor string. ``null`` means there is no more to fetch.

      .. code-block:: json
        :caption: Example response body

          {
              "next": "http://localhost:8000/api/v1/incidents/?cursor=cD0yMDIwLTA5LTIzKzEzJTNBMDIlM0ExNi40NTU4MzIlMkIwMCUzQTAw&page_size=10",
              "previous": null,
              "results": [
                  {
                      "pk": 10101,
                      "start_time": "2011-11-11T11:11:11+02:00",
                      "end_time": "2011-11-11T11:11:12+02:00",
                      "source": {
                          "pk": 11,
                          "name": "Uninett GW 3",
                          "type": {
                              "name": "nav"
                          },
                          "user": 12,
                          "base_url": "https://somenav.somewhere.com"
                      },
                      "source_incident_id": "12345",
                      "details_url": "https://uninett.no/api/alerts/12345/",
                      "description": "Netbox 11 <12345> down.",
                      "ticket_url": "https://tickettracker.com/tickets/987654/",
                      "tags": [
                          {
                              "added_by": 12,
                              "added_time": "2011-11-11T11:11:11.111111+02:00",
                              "tag": "object=Netbox 4"
                          },
                          {
                              "added_by": 12,
                              "added_time": "2011-11-11T11:11:11.111111+02:00",
                              "tag": "problem_type=boxDown"
                          },
                          {
                              "added_by": 200,
                              "added_time": "2020-08-10T11:26:14.550951+02:00",
                              "tag": "color=red"
                          }
                      ],
                      "stateful": true,
                      "open": false,
                      "acked": false
                  }
              ]
          }

      Pagination-support:

      ``next``
        The link to the next page, according to the cursor, or ``null`` if
        on the last page.

      ``previous``
        The link to the previous page, according to the cursor, or
        ``null`` if on the first page.

      ``results``
        An array of the resulting subset of rows, or an empty array if there are no
        results.

      Refer to the section :ref:`explanation-of-terms` for an
      explanation of the other fields.


   -  ``POST``: creates and returns an incident

      .. code-block:: json
        :caption: Example request body

          {
              "source": 11,
              "start_time": "2011-11-11 11:11:11.11111",
              "end_time": null,
              "source_incident_id": "12345",
              "details_url": "https://uninett.no/api/alerts/12345/",
              "description": "Netbox 11 <12345> down.",
              "ticket_url": "https://tickettracker.com/tickets/987654/",
              "tags": [
                  {"tag": "object=Netbox 4"},
                  {"tag": "problem_type=boxDown"}
              ]
          }

      Refer to the section :ref:`explanation-of-terms` for an
      explanation of the fields.


-  ``/api/v1/incidents/<int:pk>/``:

   -  ``GET``: returns an incident by primary key

   -  ``PATCH``: modifies parts of an incident and returns it

      .. code-block:: json
        :caption: Example request body

          {
              "ticket_url": "https://tickettracker.com/tickets/987654/",
              "tags": [
                  {"tag": "object=Netbox 4"},
                  {"tag": "problem_type=boxDown"}
              ]
          }

      The fields allowed to be modified are:

      -  ``details_url``
      -  ``ticket_url``
      -  ``tags``


-  ``/api/v1/incidents/<int:pk>/ticket_url/``:

   -  ``PUT``: modifies just the ticket url of an incident and returns
      it

      .. code-block:: json
        :caption: Example request body

          {
              "ticket_url": "https://tickettracker.com/tickets/987654/",
          }

      Only ``ticket_url`` may be modified.


-  ``/api/v1/incidents/<int:pk>/events/``:

   -  ``GET``: returns all events related to the specified incident

      .. code-block:: json
        :caption: Example response body

          [
              {
                  "pk": 1,
                  "incident": 10101,
                  "actor": {
                      "pk": 12,
                      "username": "nav.oslo.uninett.no"
                  },
                  "timestamp": "2011-11-11T11:11:11+02:00",
                  "received": "2011-11-11T11:12:11+02:00",
                  "type": {
                      "value": "STA",
                      "display": "Incident start"
                  },
                  "description": ""
              },
              {
                  "pk": 20,
                  "incident": 10101,
                  "actor": {
                      "pk": 12,
                      "username": "nav.oslo.uninett.no"
                  },
                  "timestamp": "2011-11-11T11:11:12+02:00",
                  "received": "2011-11-11T11:11:13+02:00",
                  "type": {
                      "value": "END",
                      "display": "Incident end"
                  },
                  "description": ""
              }
          ]

      The ``received`` parameter is set by Argus upon reception of an event. Usually,
      this is same as, or a little later, than ``timestamp`` of the incident. If there
      is a large time gap between both, or ``received`` is earlier than ``timestamp``,
      something may be wrong with the internal clock either on the argus
      server or on the event source.

   -  ``POST``: creates and returns an event related to the specified
      incident

      .. code-block:: json
        :caption: Example request body

          {
              "timestamp": "2020-02-20 20:02:20.202021",
              "type": "OTH",
              "description": "The investigation is still ongoing."
          }

      If the event is posted by an end user (a user with no associated source
      system), the ``timestamp`` field is optional. It will default to
      the time the server received the event.

      The valid ``type``\ s are:

      -  ``STA`` - Incident start

        An incident automatically creates an event of this type when
        the incident is created, but cannot have more than one. In
        other words, it’s never allowed to post an event of this
        type.

      -  ``END`` - Incident end

        Only source systems can post an event of this type, which is
        the standard way of closing an indicent. An incident cannot
        have more than one event of this type.

      -  ``CLO`` - Close

        Only end users can post an event of this type, which
        manually closes the incident.

      -  ``REO`` - Reopen

        Only end users can post an event of this type, which reopens
        the incident if it has been closed (either manually or by a
        source system).

      -  ``ACK`` - Acknowledge

        Use the ``/api/v1/incidents/<int:pk>/acks/`` endpoint.

      -  ``OTH`` - Other

        Any other type of event, which simply provides information
        on something that happened related to an incident, without
        changing its state in any way.


-  ``GET`` to ``/api/v1/incidents/<int:pk>/events/<int:pk>/``: returns a
   specific event related to the specified incident

-  ``/api/v1/incidents/<int:pk>/acks/``:

   -  ``GET``: returns all acknowledgements of the specified incident

      .. code-block:: json
        :caption: Example response body

          [
              {
                  "pk": 2,
                  "event": {
                      "pk": 2,
                      "incident": 10101,
                      "actor": {
                          "pk": 140,
                          "username": "jp@example.org"
                      },
                      "timestamp": "2011-11-11T11:11:11.235877+02:00",
                      "received": "2011-11-11T11:11:11.235897+02:00",
                      "type": {
                          "value": "ACK",
                          "display": "Acknowledge"
                      },
                      "description": "The incident is being investigated."
                  },
                  "expiration": "2011-11-13T12:00:00+02:00"
              },
              {
                  "pk": 20,
                  "event": {
                      "pk": 20,
                      "incident": 10101,
                      "actor": {
                          "pk": 130,
                          "username": "ferrari.testarossa@example.com"
                      },
                      "timestamp": "2011-11-12T11:11:11+02:00",
                      "received": "2011-11-12T11:11:11+02:00",
                      "type": {
                          "value": "ACK",
                          "display": "Acknowledge"
                      },
                      "description": "The situation is under control!"
                  },
                  "expiration": null
              }
          ]


   -  ``POST``: creates and returns an acknowledgement of the specified
      incident

      .. code-block:: json
        :caption: Example request body

          {
              "event": {
                  "timestamp": "2011-11-11 11:11:11.235877",
                  "description": "The incident is being investigated."
              },
              "expiration": "2011-11-13 12:00:00"
          }

      Only end users can post acknowledgements.

      The ``timestamp`` field is optional. It will default to
      the time the server received the event if omitted.


-  ``GET`` to ``/api/v1/incidents/<int:pk>/acks/<int:pk>/``: returns a
   specific acknowledgement of the specified incident

-  ``/api/v1/incidents/sources/``:

   -  ``GET``: Returns a list of all sources

      .. code-block:: json
        :caption: Example response body

        [
          {
            "pk": 1,
            "name": "argus",
            "type": {
              "name": "argus"
              },
            "user": 1,
            "base_url": ""
          }
        ]


-  ``GET`` to ``/api/v1/incidents/mine/``: behaves similar to
   ``/api/v1/incidents/``, but will only show the incidents added by the
   logged-in user, and no filtering on source or source type is
   possible.

-  ``GET`` to ``/api/v1/incidents/open/``: returns all open incidents

-  ``GET`` to ``/api/v1/incidents/open+unacked/``: returns all open
   incidents that have not been acked

-  ``GET`` to ``/api/v1/incidents/metadata/``: returns metadata
   for all incidents


Notification profile endpoints
------------------------------

-  ``/api/v1/notificationprofiles/``:

   -  ``GET``: returns the logged in user’s notification profiles

   -  ``POST``: creates and returns a notification profile which is then
      connected to the logged in user

      .. code-block:: json
        :caption: Example request body

          {
              "timeslot": 1,
              "filters": [
                  1,
                  2
              ],
              "media": [
                  "EM",
                  "SM"
              ],
              "phone_number": 1,
              "active": true
          }

      The ``phone_number`` field is optional and may also be null.


-  ``/api/v1/notificationprofiles/<int:pk>/``:

   -  ``GET``: returns one of the logged in user’s notification profiles
      by primary key

   -  ``PUT``: updates and returns one of the logged in user’s
      notification profiles by primary key

      -  Note that if ``timeslot`` is changed, the notification
         profile’s primary key will also change. This consequently means that the
         URL containing the previous primary key will return a ``404 Not Found``
         status code.
      -  Example request body: same as ``POST`` to
         ``/api/v1/notificationprofiles/``

   -  ``DELETE``: deletes one of the logged in user’s notification
      profiles by primary key

-  ``GET`` to ``/api/v1/notificationprofiles/<int:pk>/incidents/``:
   returns all incidents - both open and historic  - filtered by one of
   the logged in user’s notification profiles by primary key

-  ``/api/v1/notificationprofiles/timeslots/``:

   -  ``GET``: returns the logged in user’s time slots
   -  ``POST``: creates and returns a time slot which is then connected
      to the logged in user

      .. code-block:: json
        :caption: Example request body

          {
              "name": "Weekdays",
              "time_recurrences": [
                  {
                      "days": [1, 2, 3, 4, 5],
                      "start": "08:00:00",
                      "end": "12:00:00"
                  },
                  {
                      "days": [1, 2, 3, 4, 5],
                      "start": "12:30:00",
                      "end": "16:00:00"
                  }
              ]
          }


      The optional key ``all_day`` indicates that Argus should use
      ``Time.min`` and ``Time.max`` as ``start`` and ``end``
      respectively. This also overrides any provided values for
      ``start`` and ``end``. An example request body:

      .. code:: json

          {
              "name": "All the time",
              "time_recurrences": [
                  {
                      "days": [1, 2, 3, 4, 5, 6, 7],
                      "all_day": true
                  }
              ]
          }

      which would yield the response:

      .. code:: json

          {
              "pk": 2,
              "name": "All the time",
              "time_recurrences": [
                  {
                      "days": [1, 2, 3, 4, 5, 6, 7],
                      "start": "00:00:00",
                      "end": "23:59:59.999999",
                      "all_day": true
                  }
              ]
          }


-  ``/api/v1/notificationprofiles/timeslots/<int:pk>/``:

   -  ``GET``: returns one of the logged in user’s time slots by primary key
   -  ``PUT``: updates and returns one of the logged in user’s time
      slots by primary key

      Example request body: same as ``POST`` to
         ``/notificationprofiles/timeslots/``

   -  ``DELETE``: deletes one of the logged in user’s time slots by primary key


-  ``/api/v1/notificationprofiles/filters/``:

   -  ``GET``: returns the logged in user’s filters
   -  ``POST``: creates and returns a filter which is then connected to
      the logged in user

      .. code-block:: json
        :caption: Example request body

          {
              "name": "Critical incidents",
              "filter_string": "{\"sourceSystemIds\": [<SourceSystem.pk>, ...], \"tags\": [\"key1=value1\", ...]}"
          }


-  ``/api/v1/notificationprofiles/filters/<int:pk>/``:

   -  ``GET``: returns one of the logged in user’s filters by primary key
   -  ``PUT``: updates and returns one of the logged in user’s filters
      by primary key

      Example request body: same as ``POST`` to
         ``/api/v1/notificationprofiles/filters/``

   -  ``DELETE``: deletes one of the logged in user’s filters by primary key


-  ``POST`` to ``/api/v1/notificationprofiles/filterpreview/``: returns
   all incidents - both open and historic - filtered by the values in
   the body

   .. code-block::
    :caption: Example request body

       {
           "sourceSystemIds": [<SourceSystem.pk>, ...]
       }
