Models
------

.. _explanation-of-terms:

Explanation of terms
~~~~~~~~~~~~~~~~~~~~

-  ``incident``: an unplanned interruption in the source system.
-  ``event``: something that happened related to an incident.
-  ``acknowledgement``: an acknowledgement of an incident by a user,
   which hides the incident from the other open incidents.

   -  If ``expiration`` is an instance of ``datetime``, the incident
      will be shown again after the expiration time.
   -  If ``expiration`` is ``null``, the acknowledgement will never
      expire.
   -  An incident is considered “acked” if it has one or more
      acknowledgements that have not expired.

-  ``start_time``: the time the ``incident`` was created.
-  ``end_time``: the time the ``incident`` was resolved or closed.

   -  If ``null``: the incident is stateless.
   -  If ``"infinity"``: the incident is stateful, but has not yet been
      resolved or closed - i.e. open.
   -  If an instance of ``datetime``: the incident is stateful, and was
      resolved or closed at the given time; if it’s in the future, the
      incident is also considered open.

-  ``source``: the source system that the ``incident`` originated in.
-  ``object``: the most specific object that the ``incident`` is about.
-  ``parent_object``: an object that the ``object`` is possibly a part
   of.
-  ``problem_type``: the type of problem that the ``incident`` is about.
-  ``tag``: a key-value pair separated by an equality sign (=), in the
   shape of a string.

   -  The key can consist of lowercase letters, numbers and underscores.
   -  The value can consist of any length of any characters.

ER diagram
~~~~~~~~~~

.. figure:: img/ER_model.png
   :alt: ER diagram

   ER diagram
