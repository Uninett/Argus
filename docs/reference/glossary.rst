.. _explanation-of-terms:

====================
Explanation of terms
====================

Terms used in Argus are loosely based on the `ITIL standard
<https://en.wikipedia.org/wiki/ITIL>`_ for IT service management.

.. glossary::
   :sorted:

   incident
      an unplanned interruption in the source system

   event
      something that happened related to an incident.

   acknowledgement
      an acknowledgement of an incident by a user, which hides the incident
      from the other open incidents.

   expiration
      When, if ever, an acknowledgement ceases to be in effect.

      - If ``expiration`` is an instance of ``datetime`` (for example
        ``2011-11-11T11:11:11+02:00``), the incident will be shown again after
        the expiration time.
      - If ``expiration`` is SQL ``null``, represented in code as Python
        ``None``, the acknowledgement will never expire.
      - An incident is considered “acked” (acknowledged) if it has one
        or more acknowledgements that have not expired.

   start_time
      the time the incident was created.

   end_time
      the time the incident was resolved or closed.

      - If the value is an instance of ``datetime`` the incident is stateful,
        and was resolved or closed at the given time. If the end time is in the
        future, the incident is considered still open.
      - If ``null`` the incident is stateless (i.e. it cannot be closed).
      - If ``"infinity"`` the incident is stateful, but has not yet been
        resolved or closed - for example, if it is still open.

   source
      the source system that the incident originated in.

   tag
      a key-value pair in the form of ``key=value``.

      - The key can consist of lowercase letters, numbers and underscores.
      - The value can consist of any length of any characters.

   primary key
      Abbreviated as ``pk`` or ``<int:pk>``.

      Argus uses “primary keys” to uniquely identify users, phone numbers,
      incidents, incident source systems, notification profiles, timeslots and
      similar. A primary key is a non-negative integer number. It is unique by
      the context it refers to (for example, phone numbers' ``pk``\ s are
      unique for each user).

   filter
      Filters are used to:

      - Limit which incidents are returned via the API.
      - Check whether notifications should be sent when a new incident is
        registered or when an existing incident is changed via an event.

   Filter.filter
      A single filter is stored in the Filter model's ``filter``-attribute, as
      JSON.

   FilterBlobSerializer
      What filters look like and what they do is customizable. This serializer
      validates and represents the structure of a filter stored in
      ``Filter.filter``.

   tristate
      A value that can be one of ``True``, ``False``, or ``None``. Used in
      filters. A stateful incident can be open or closed, but an incident
      filter can look for incidents that are either open, closed or ignore the
      distinction.

   stateful incident
      A stateful incident can be open (still open to change) or closed
      (probably won't change). A stateful incident has both a ``start_time``
      and an ``end_time`` and the time in between is a ``duration``.

   stateless incident
      A stateless incident can neither be open nor closed, nor can it have
      a duration. It is a moment in time, well suited for heart-beats and
      one-off messages. A stateless incident uses the ``start_time``-field to
      store when it happened.
