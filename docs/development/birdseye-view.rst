=================
A bird's eye view
=================

.. graphviz:: birdseye-view.dot

Sources
=======

A source pushes incidents to the argus server via the API. Changes to those
incidents are done via pushing events. An incident has a field
``incident_source_id`` for storing an id, for changing an already existing
incident by adding an event.

Glue-service
------------

A glue-service runs independently of the argus server. It sits between a source
and the argus server and translates an incident from the source to the API. The
``incident_source_id`` for the incident is copied from the source if available
or otherwise handled by the glue-service.

The glue-service can either be built in to the source, or be completely
standalone and pull changes from the source before it pushes them on.

Agent
-----

An agent can change existing incidents (by adding events) or create new
incidents by analyzing already existing incidents and events.

It is standalone.

Frontend
========

The frontend fetches a list of incidents according to a user-created filter. It
allows the user to create such filters, to set up notification profiles
using these filters, and to set up destinations to be used in the profiles.

Notification system
===================

A user has one or more notification profiles.

A notification profile is used by the server for sending notifications about
a chosen subset of the incidents. It consists of one or more filters, one or
more timeslots (for which periods of the day a profile is valid) and one or
more destinations.

Destination
-----------

A destination is a plugin to argus server. It stores its config in the
"DestinationConfig"-model. See :doc:`/writing-plugins`.

Server
======

The server receives incidents from sources, provides access to the accumulated
list of incidents via API, and matches incidents to notification profiles.
Matched incidents are sent to the destinations listed in the profiles.

There is a non-API admin-interface for the registration of sources and admin
users.
