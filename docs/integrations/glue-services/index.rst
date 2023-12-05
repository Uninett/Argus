==========================================
Integrating monitoring software with Argus
==========================================

In essence, to integrate your existing monitoring systems with Argus means to
ensure your Argus incident database is synchronized with the alerts stemming
from your monitoring systems.

To ensure this, you will need what is termed a **glue service**.

Glue services
=============


What is a glue service?
-----------------------

A *glue service* is any piece of software capable of receiving alerts from your
monitoring system and translating these into incident state changes that are
communicated to the Argus API server.

A glue service for your particular monitoring system may already exist, or you
may need to write your own.

Existing glue services
----------------------

* Network Administration Visualized: https://github.com/Uninett/nav-argus-glue.
  This is an extension of nav, runs on the same server, and uses the NAV config
  files.
* NAGIOS:

  * There's a python script at https://github.com/SUNET/nagios-argus-glue. It
    didn't scale to SUNET's needs.
  * There's the code for a tiny rust binary at https://github.com/SUNET/nglue
    that is run by NAGIOS. It sends alerts to
    https://github.com/SUNET/nglue-api, designed to run in a container. The
    nglue-api pre-filters what to send to argus.
* Mist Systems Administration (Juniper): https://gitlab.sikt.no/cnaas/mist-argus

Integrating an existing monitoring system
=========================================

Each instance of a monitoring system that delivers incidents to Argus is known
in Argus as a *source system*. Regardless of whether glue service software
exists for your system, or you need to write your own, you must make Argus
aware of this source system. This is accomplished in the *Admin* interface of
the Argus API server, reachable at
`https://your-argus-server-here/admin/`. Here you need to

* Add a new Source System

  1. Select an identifiable name for this source system. For web based
     systems, it is common to use the FQDN of the web service here.
  2. Select a system type, creating a new one if necessary. The only
     significance of this at the moment is the ability to categorize multiple
     instances of the same software type.
  3. For source systems that are reachable via a web URL, you can add a base
     URL. All relative URLs referenced in incidents posted by this source
     system will have this base URL prefixed.
  4. Optionally, select a username for this system's system user in Argus. If
     left blank, Argus will use the system name you entered in the first
     field.
  5. Save the new source system.

* Create a new API authentication token for the new source system

  1. Select :guilabel:`Add` under the :guilabel:`Auth token` section in the
     admin interface.
  2. Find the system user that was created for your source system in the
     :guilabel:`User` dropdown and click the plus sign.
  3. Make note of the long hexadecimal token that was generated. You will need
     this when configuring Argus API access in your glue service. Any incident
     posted to the Argus API using this token will be associated with this
     source system. **Keep the token a secret!**

   .. note::

     It is very important to ensure that the token is always valid. This can
     be ensured by using the management command :ref:`check-token-expiry`,
     which makes argus post an incident if there are any tokens that will
     expire soon.

     If a token is not valid it will currently lead to the source system
     not being able to report incidents without any warnings.

Writing your own glue service
=============================

If there is no pre-existing glue service software for your particular
monitoring system, we've provided a :doc:`guide for writing your own
<writing-glueservices>`.

.. toctree::
   writing-glueservices
