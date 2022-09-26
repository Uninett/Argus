==============================
Writing your own glue services
==============================

Writing a glue service has a few requirements:

1. Knowing how to integrate with your monitoring system so that your glue
   service will be notified of all alerts.
2. Knowing how to use the Argus API.

We can only provide hints for how to think about number 1. This guide will
therefore mostly focus on the second requirement.

How to get alerts from your monitoring system
=============================================

This depends entirely on your source system and what mechanisms it provides for
this. Some systems, like `NAV`_, will provide scripting hooks for receiving raw
streams of all alerts and state changes that occur. Others will provide
scripting hooks as part of its notification systems. Some systems may even be
as simple as cron jobs that only send e-mails on errors and keep no internal
state.

Things you need to consider:

* Does your system keep track of its own alert states, or is every notification
  stateless? If your system keeps state, what is the state identifier? This
  identifier should be part of the incident posted to Argus, as means to ensure
  you are keeping Argus in sync with your source system.
* Do you need or want to backfill a history of incidents from your source
  system, from before your integration with Argus, or do you only care about
  new incidents?
* What happens if the communication between your glue service and Argus
  temporarily breaks down? How will you synchronize the Argus incident database
  with everything that happened in your source system during this outage?
  Strategies may include:

  * Your glue service maintains its own persistent queue of unsynchronized
    incidents and makes sure to flush this once communication with Argus is
    restored.
  * Your source system maintains its own logs of state changes, which can be
    used as a data source to synchronize Argus once communication is restored.


.. _NAV: https://nav.uninett.no/

Argus API access libraries
==========================

If you prefer to work with Python, you are in luck: There is already a Python
library to help you access and consume the Argus API, called `PyArgus`_
(available on PyPI as `argus-api-client`_).

.. _PyArgus: https://github.com/Uninett/pyargus/
.. _argus-api-client: https://pypi.org/project/argus-api-client/


Incidents and the Argus API
===========================

Argus models **Incidents**. An incident will, in most cases, be stateful,
meaning it's either open or closed, and has both a **start timestamp** and an
**end timestamp**. An open, stateful incident is represented by a value of
``infinity`` in its end timestamp. Stateless incidents are also supported by
Argus, but are not the main focus of the API and UI (See `On stateful
incidents vs. stateless incidents`_ for details).

An incident has a **description**, which is a string of text, usually derived
from the source system, to describe a problem that happened.

An incident can have any number of **tag** values. These are useful metadata to
categorize an incident, and thereby filtering it in either the Argus frontend
dashboard or in a user's notification profile.

A glue service mainly concerns itself with:

* Creating new incidents in Argus whenever a source system reports a problem.
* Describing and tagging created incidents in an expressive, meaningful way for
  the users' consumption.
* Closing existing Argus incidents it has created when the source system
  reports that a problem has been resolved.

Creating a new incident
-----------------------

Creating a new incident in Argus is done by **POST**-ing a JSON payload to the
REST API endpoint ``/api/v1/incidents/`` (See the :ref:`api-incident-endpoints`
documentation).

At minimum, you need to provide these incident attributes:

* ``decription``
* ``start_time``
* ``tags``
* To indicate that this incident is stateful (meaning it is waiting to be
  resolved), you must also give the ``end_time`` attribute the value
  ``"infinity"``. If you don't do this, ``end_time`` will default to a ``null``
  value, which means this incident is *stateless*, and does not need to be
  resolved.

Optionally, you may want to provide these attributes as well:

* ``source_incident_id``: An identifier that can be used to match up this
  incident with some state/alert/incident in the source system in the
  future. If provided, Argus will enforce uniqueness of source incident
  identifiers.
* ``details_url``: A relative (or fully-qualified) URL to a page in the source
  system's web-based user interface, which will give more details about this
  specific incident.


.. code-block:: json
   :caption: Complete example of an incident JSON payload

   {
       "description": "foobar-sw.example.org stopped responding to ping requests",
       "source_incident_id": "42",
       "details_url": "/alerts/detail/42/",
       "start_time": "2020-12-11 15:50:42",
       "end_time": "infinity",
       "tags": [
	 {"tag": "host=foobar-sw.example.org"},
	 {"tag": "location=Campus Rotvoll"},
	 {"tag": "customer=himunkholmen.no"}
       ]
   }

Describing an incident through tags
-----------------------------------

Using tags to describe your incidents is a good idea. Tags can be used to
describe almost any structured or unstructed incident metadata not covered by
the standard incident attributes.

Examples include:

* The hostname of an affected device.
* A reference to an affected customer.
* A geographical location where the problem occurred.
* A reference to an affected service instance.
* A URL to a relevant section of the affected service's operating instructions.

This kind of metadata will enable:

* Your first line of support to correctly assess, prioritize and react to
  incidents.
* Once Argus gains proper integration with ticketing systems, the metadata in
  tags can also be carried forward automatically to tickets.
* Your devops teams can create notification filters specifically for the
  services, devices or customers they care about.
* Generating reports and statistics on the number and duration of incidents per
  service, per customer, per device and so forth.

Tag syntax
~~~~~~~~~~

Incident tags are defined syntactically as ``key=value``. This syntax is
employed by the API both when posting and retrieving incident tags. Any
alphanumeric string (excluding spaces and the ``=`` character itself) can be
used as a tag *key*, whereas the value can be any string.


On the importance of tag conventions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When integrating multiple types of source systems into Argus, it is important
to implement a convention for which tag keys to use, so that the incidents
reported by your monitoring systems are consistent.

You may, for example, have two separate monitoring systems that monitor
different aspects of the device ``foobar-sw.example.org``. If one system
reports incidents with the tag ``host=foobar-sw.example.org``, and the other
uses ``fqdn=foobar-sw.example.org``, then you will just have a mess on your
hands.

Closing incidents that have been resolved
-----------------------------------------

Once the source system reports an incident as resolved, the glue service
needs to close the corresponding Argus incident. But how can it keep track of
which Argus incident maps to the resolved problem?

There could be a multitude of approaches to this, but in essence there are two
distinct scenarios that come into play:

- The source system already keeps track of its own state.
- The source system does not keep track of state.

When the source system already tracks state
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this scenario, the source system should already have some identifier for the
resolved state, and you should already have posted this value in the
``source_incident_id`` when you first created the Argus incident.

The API endpoint ``/api/v1/incidents/mine/`` is useful in this regard. It
functions mostly the same as the ``/api/v1/incidents/`` endpoint, but will only
ever look at incidents reported from the source system whose API token you are
currently using to access the API.

If your source system reports that it resolved a problem whose identifier was
``42``, you can simply find the corresponding Argus incident by issuing a
**GET** request for ``/api/v1/incidents/mine/?source_incident_id=42``.

When the source system does not track internal state
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this case, things immediately become more involved. Your glue service needs
a strategy to track state itself. Suggested strategies may be:

* The glue service needs to track state in its own database.
* The glue service can potentially calculate a hash value of incident
  attributes that will be the same for events that close an incident as for
  events that open an incident. This hash value can be used as the Argus
  incident's ``source_incident_id``, and then use the same strategy as for
  state-tracking source systems.
* The glue service can fetch the list of open Argus incidents posted by itself
  (from ``/api/v1/incidents/mine/?open=true``), then use as complicated a
  custom algorithm as necessary to determine which of these Incidents match up
  with the resolving event it is currently processing.

Performing the close operation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Closing an open Argus incident normally entails changing the incident's
``end_time`` attribute to a proper timestamp (representing the time the source
system detected that the incident had been resolved).  However, Argus will not
simply allow you to set this value on an existing incident.

Instead, Argus keeps *a log of events for each incident* it tracks. When you
created the original incident, a creation event was implicitly logged alongside
it. An Argus incident is closed by posting a closing event to the incident's
event log. The closing event can contain its own description, if need be.

An incident with the id ``27`` can be closed by **POST**-ing a new event to
``/api/v1/incidents/27/events/``:

.. code-block:: json

   {
     "timestamp": "2020-12-11 15:57:00",
     "type": "END",
     "description": "Foobar was resolved somehow"
   }

You should only ever use the ``END`` event type to indicate that the incident
was resolved from the source system.  The available types of events are
documented in :ref:`api-incident-endpoints`.


On stateful incidents vs. stateless incidents
=============================================

Argus incidents are primarily *stateful*, but the concept of *stateless*
incidents is also supported. The difference may not be immediately obvious, and
depending on your needs, stateless incidents may seem useless.

Stateful incidents
------------------

A stateful incident, by definition, has an extent in time. The incident began
at some point in time, and ended (or *will* end) at a later point in time. The
*state* of an such an incident is therefore either *open* or *closed*.

An incident must always have a ``start_time`` value. If a definite ``end_time``
value has not been set for it yet, its state is considered **open**. Once a
definite ``end_time`` value is set, it is considered **closed**.

Stateless incidents
-------------------

A stateless incident only represents something that happened at a single point
in time, and otherwise has *no extent in time*. It can never be considered to
be *open* nor *closed*.

Whether stateless incidents are useful to you depends on your needs and the
source systems you want to integrate with Argus. Some source systems will
generate alerts that are just one-off notifications, and are not considered to
represent a state or an ongoing problem.

One such example is from *Network Administration Visualized* (NAV), which will
send one-off early warnings that devices have stopped responding to ICMP ping
requests. These are sent a few minutes in advance of NAV actually declaring the
device to be down/non-responsive. If several such warnings messages are sent,
while the device is never actually declared to be down, this may indicate that
there is a problem with "flapping", even though the device appears to be
responding most of the time.

Stateless incidents can be matched by notification profiles, if so desired. The
Argus API incidents endpoint (and the Argus UI) will, by default, only show
open/stateful incidents unless explicitly instructed to also include stateless
incidents. Normally, open stateful incidents are the ones you want to act on.


Representation
--------------

Internally, to represent a stateful incident that is still open, the special
value ``infinity`` is used as the value of ``end_time``. This signals that the
incident is expected to end at some unknown point in the future, and is quite
useful when doing time-based queries on stateful incidents.

Conversely, stateless incidents will never have an ``end_time`` value, which
means that these incidents explicitly set this to a ``null`` value.

These special values are also exposed through the API.
