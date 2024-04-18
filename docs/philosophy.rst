==========================
The philosopy behind Argus
==========================

Background
==========

There was a *long* debate about what to call the primary object of study in Argus:

* alert
* alarm
* incident
* happening
* event
* .. se synonym dictionary for more

As it turns out, different groups use different terms, and even if they use the
same term, they have different expectations and definitions. We chose
"incident", which consists of one or more "events", and our "incident" is as
simple as we could make it.

An *incident* is reported (pushed) by a machine *source*. That source has a *type*. Any
change in the incident at the source is reported by the source as an *event*.
Any changes done by humans on a specific incident are also reported as an
*event*. The machine source can categorize incidents via *tags*, but argus does
not know or care what the tags mean. *Notifications* can be set up via
*filters* for a subset of the events.

Argus was started to solve three problems:

1. To aggregate/collect incidents from multiple NAV's without having to
   fundamentally break the philosopy of NAV
2. To have a filter system that does not need mathematics at university level
   or a full day's class or more to understand and use, hence: no Boolean
   expressions [1]_
3. To be able to send notifications for a subset of the collected alarms/alerts/incidents [2]_

Because our definition of incident is so simple, and since it is the source
that is in control of when and where to send incidents, it was easy to add
other sources than NAV, so we did.

Manifesto
=========

Argus aims to be a small tool in the Unix tradition, though it aims to do three
things well:
  * store incidents and their events
  * filter incidents and their events
  * notify about incidents and their events

* Argus is not an inventory system
* Argus is not a monitoring system, real-time or other
* There is no pull. The source pushes incidents, argus pushes notifications.
* Argus. Will. Not. Spam.

.. rubric:: Footnotes

.. [1] There is of course Boolean logic underlying the filters but we will
   never allow the full expressitivity
.. [2] There is no way to send notifications for ALL incidents/events. The
   closes you can get is sending for all stateful incidents, which will then
   not allow sending for stateless incidents.
