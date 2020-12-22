===========
About Argus
===========

Introduction
------------

IT operations these days tend to be complex affairs, and rarely does any
organization get by with only a single monitoring system for everything. Even
though some of these systems are quite extensible, and can meet many of an IT
operator's needs, you inevitably end up with multiple software systems to cover
your entire IT infrastructure.

All of these systems produce alerts, and will invariably provide their own
facilities for conveying these alerts to its human operators, either through
web-based dashboards or push notifications to e-mail, mobile phones or direct
messaging services. As the number of monitoring systems keep increasing, so
does the complexity of managing notifications from all of them. Getting a
complete picture of all incidents in your infrastructure becomes quite the
chore.

For this reason, the *Argus alert aggregator* was born.

At Uninett, not only do we have multiple monitoring systems, but as we provide
monitoring as a service for customers, we increasingly have multiple instances
of the same monitoring systems. We needed some way to aggregate all the alerts
that are being produced into a single, coherent dashboard system. This would
give our first line of support, the Uninett Service Center, an overview of all
the currently active incidents across all or services, and a single place to
manage notification profiles for both the first line and second line support
teams.

Argus tries to adhere to the principle of *single responsibility*, i.e. Argus
does not perform any monitoring itself: It acts simply as an aggregator of
current and past incidents in your IT infrastructure, dispatching notifications
as incidents are opened and closed. Argus does not actively retrieve incidents
from third party services, but relies on reports delivered to it through the
API.


The API and the user interface
------------------------------

In keeping with the single responsibility principle, a complete Argus setup
consists two separate components, with separate concerns: The Argus API server,
and the Argus frontend.

The Argus server does not provide a user interface (with the exception of the
auto-generated admin interface), but instead provides a REST API to interact
with the incidents database and the database of user notification profiles.

The `Argus frontend application`_ acts as an Argus API client to provide humans
with a web-based user interface. This user interface allows humans to interact
with the contents of the Incident database, and to configure their personal
notification profiles.

These documentation pages chiefly describe how to use the Argus API server,
while frontend application documentation is provided separately.


The Argus server admin interface
--------------------------------

The Argus server **does**, however, provide an auto-generated administration
interface. This is, however, not directed at regular users, but to Argus admins
that need to perform low-level administration tasks on a running Argus server,
such as:

* Administration of Argus user accounts
* Creating API authentication tokens for users
* Defining new source systems


.. _`Argus frontend application`: https://github.com/Uninett/argus-frontend
