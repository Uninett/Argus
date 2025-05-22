===========
About Argus
===========

Introduction
------------

IT operations these days tend to be complex affairs, and rarely does any
organization get by with only a single monitoring system for everything. Even
though some of these systems are extensible, and can meet many of an IT
operator's needs, organizations inevitably end up with multiple software
systems to cover their entire IT infrastructure.

All of these systems generate alerts, and provide their own facilities for
conveying these alerts to their human operators, either through web-based
dashboards or push notifications to e-mail, mobile phones or direct messaging
services. As the number of monitoring systems keep increasing, so does the
complexity of managing notifications from all of them. Getting a complete
picture of all incidents in the infrastructure becomes challenging.

For this reason, the *Argus alert aggregator* was developed.

At Sikt, not only do we have multiple monitoring systems, but as we provide
monitoring as a service for customers, we often have multiple instances of the
same monitoring systems. Our aim was to aggregate all alerts into a single,
coherent dashboard system. This dashboard provides a comprehensive overview of
all currently active incidents across all services to our first line of
support, the Sikt Service Center. It serves as a single place to manage
notification profiles for both the first and second line support teams.

Argus follows the principle of *single responsibility*, i.e. it does not
perform any monitoring itself. It acts as an aggregator of current and past
incidents in IT infrastructure. It dispatches notifications when incidents
are opened and closed. Argus does not actively retrieve incidents from third
party services, but relies on reports delivered to it through the API. These
services are called *source systems*.


The API
-------

Argus provides a REST API to interact with the incident database and the
database of user notification profiles. It handles incidents received from
source systems, and allows viewing and processing them via the REST API.

It also supports setting up user-specific notification profiles, and sends
notifications to users based on said profiles.

It is complete enough to build a separate frontend as a single page application
(SPA).

The user interface
------------------

The Argus frontend acts as a client to provide end users with a web-based user
interface to Argus. Using the frontend, users can view, filter and interact
with the contents of the incident database, and create personal notification
profiles conveniently in their web browsers.

The Argus admin interface
-------------------------

Besides the REST API, Argus has an administration interface.
It can be used to perform low-level administration tasks on a running Argus
server, such as:

* Administration of Argus user accounts
* Creating API authentication tokens for users
* Defining new source systems to collect incidents from

Pick and choose
---------------

It is possible to run only the API, only the frontend (given that it has access
to a database receiving incidents by something else) or both at the same time
and in the same deployment.
