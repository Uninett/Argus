===========================================
Howto: Safely test sending of notifications
===========================================

By "safely test" we mean "not accidentally spamming anyone with test incidents".

Automated tests are well and good, but filters especially can be complex things
and can behave in what for users is an unexpected way. (The problem sometimes
does exist between keyboard and chair.)

The techniques here are suitable both for problems in production, new types of
filters, unexpected behaviours, refactors of the entire shebang, and working
out how things actually work in order to improve automated tests.

Testing filters, profiles, timeslots regardless of destination type
===================================================================

When doing a test of everything *except* details of the destination type, use
the standard email medium
(``argus.notificationprofile.media.email.EmailNotification``) as the sole
destination type. Adapt or create a profile accordingly.

Automated tests
---------------

Use the `override_settings`_ decorator to override the setting
``MEDIA_PLUGINS`` with the exact list of media the test will need.

Redirect email to console
=========================

Do not actually send those notification emails, catch them locally.

There are two ways of doing this:

1. Changing the EMAIL_BACKEND setting to
   ``django.core.mail.backends.console.EmailBackend``. Sending an email will
   then turn up in some terminal window somewhere.
2. Sending to an email server you control, the easiest is to send it to one
   set up for the test. Set ``EMAIL_HOST`` to ``localhost``, ``EMAIL_PORT`` to
   ``1025``, and run a dummy mailserver::

      $ python -m smtpd -n -c DebuggingServer localhost:1025

  Sent notifications will then be dumped to the console where the dummy server
  runs.

The former method works less well with docker since it can be tricky to find
the correct container that has the dump of the email, plus there's usually so
much going on in the console of the container that finding the message might be
tricky. With the latter method the email is dumped in the window the
DebuggingServer is running in, which allows a little more control.

One of the two methods above is probably what you want for your
development-setup regardless.

Automated tests
---------------

Use the `override_settings`_ decorator to override the setting
``EMAIL_BACKEND`` and use method 1 above.

Testing something that fails in production
==========================================

Copy the profiles to your debugging-setup. You can just reuse your
development-setup for this: move the dev-database out of the way (for instance
with the ``ALTER DATABASE .. RENAME`` statement), dump the production database,
then import the dump into your dev-database.

Deactivate profiles you are not testing
=======================================

Deactivating profiles prevents spam, makes the test go faster since there is
less to test, and makes it easier to find the result in the console since less
will be printed. (Don't do this in production regardless.)

Find the ids of the profiles you want to test first. Let's assume you'll be
testing profiles "1" and "22".

There are several methods:

1. Deactivate all others in the admin.
2. If you have access to the database, deactivate via ``python manage.py dbshell``::

        argus=> UPDATE argus_notificationprofile_notificationprofile SET active = false WHERE id NOT IN (1, 22);
3. You can deactivate via the python shell as well, launch with ``python
   manage.py shell``::

       > from argus.notificationprofile.models import NotificationProfile
       > NotificationProfile.objects.exclude(id__in=(1, 22)).update(active=False)

With option 1 you need an authenticated user in the system that has both
``is_staff`` and ``is_superuser`` set to ``True``. For all the others you need
database access.

Automated tests
---------------

Use factories to create exactly what to test. You can recreate a scenario in
the production database exactly with the factories, then when the test works,
adjust the factory to only set exactly the subset of attributes needed.

Testing specific destination types
==================================

If the plugin has a dummy version that just dumps to the console, see if
testing with that dummy is sufficient. Otherwise you need to find a test
destination (in order to not spam the production destination). For instance
with the MS teams-plugin set it up to spam a test-channel or yourself.

If the live test works but pushing to the production destination does not, it's
probably a permissions-problem.

Email is not delivered
----------------------

If an email is not delivered even if the email server logs of the first hop
(the one set as ``EMAIL_HOST``) says the email was received, it is probably one
of three things:

1. Something is wrong with the first hop, like a missing or outdated
   certificate, wrong entry in DNS, missing DKIM/SPF/DMARC, missing reverse DNS
   lookup, the IP address is on a blacklist. The possibilities are nearly
   endless.
2. Something is wrong at the final hop (the email server receiving for the
   domain in the ``To:``-address)
3. Something is wrong in between. Network, DNS, other email servers along the
   route...

This is not something you can solve alone. Send a fake incident to the failing
email address with the normal email backend in settings and use that to find
the exact:

* date and time the non-delivered email was sent (do not forget the timezone)
* the ``To:``-address
* the ``From:``-address

Give this to your postmaster (the person or persons responsible for/monitoring
the email system). That should be enough for them to sometimes solve case #1.

Making test incidents to trigger the notification system
========================================================

While it is possible to sit in the python shell and create everything by hand
for 100% control, most of the time it is sufficient to use one of the below
methods:

1. In the admin, go to the ``Incidents`` model in the "ARGUS_INCIDENT" section.
   There's a button "FAKE INCIDENT" just left of the "ADD INCIDENT"-button.
2. From the command line use the ``create_fake_incident`` command with ``python
   manage.py``.

We do not recommend making an incident directly in the database, because the
event that triggers the notification is made by Python.

.. _override_settings: https://docs.djangoproject.com/en/4.2/topics/testing/tools/#django.test.override_settings
