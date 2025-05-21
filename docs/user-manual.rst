User’s guide to Argus
=====================

-  `About Argus <#what-is-argus>`_
-  `Log in <#log-into-argus>`_

   -  `Using username and
      password <#login-using-username-and-password>`_
   -  `Using OAuth
      2.0 <#login-using-oauth-20-feide-in-the-example-below>`_
   -  `Debugging network errors <#debugging-network-errors-on-login>`_

-  `Manage alarms <#work-with-alarms-in-argus>`_

   -  `What is an incident <#what-is-an-incident-in-argus>`_
   -  `Access detailed incident view <#access-detailed-incident-view>`_
   -  `Work with table <#work-with-incidents-table>`_

      -  `Change rows per
         page <#change-how-many-rows-are-shown-per-incidents-table-page>`_
      -  `Navigate table <#navigate-incidents-table>`_
      -  `Change refresh
         interval <#change-how-often-incidents-table-gets-refreshed>`_

   -  `Filter
      incidents <#decide-which-incidents-are-shown-in-the-table>`_

      -  `Filter by open/close <#filter-by-openclose-status>`_
      -  `Filter by
         acknowledgement <#filter-by-acknowledgement-status>`_
      -  `Filter by sources <#filter-by-source-monitoring-system>`_
      -  `Filter by tags <#filter-by-tags>`_
      -  `Filter by severity level <#filter-by-severity-level>`_
      -  `Filter out old incidents <#filter-out-older-incidents>`_

   -  `Work with stored filters <#work-with-stored-filters>`_

      -  `Save filter <#save-current-filter>`_
      -  `Modify filter <#modify-existing-filter>`_
      -  `Apply filter <#apply-existing-filter>`_
      -  `Unselect applied filter <#unselect-applied-filter>`_
      -  `Delete filter <#delete-existing-filter>`_

   -  `Update one incident <#update-one-incident>`_

      -  `Re-open closed (resolved)
         incident <#re-open-a-closed-resolved-incident>`_
      -  `Close (resolve) incident <#close-resolve-an-incident>`_
      -  `Acknowledge incident <#add-acknowledgement-to-an-incident>`_
      -  `Update ticket <#update-incident-ticket>`_

         -  `Manually add ticket to
            incident <#manually-add-ticket-url-to-an-incident>`_
         -  `Edit ticket URL <#edit-ticket-url>`_
         -  `Remove ticket from
            incident <#remove-ticket-url-from-an-incident>`_
         -  `Automatically generate ticket from
            incident <#automatically-generate-ticket>`_

   -  `Update several incidents <#update-several-incidents-at-a-time>`_

      -  `Re-open incidents <#re-open-closed-resolved-incidents>`_
      -  `Close incidents <#close-resolve-incidents>`_
      -  `Acknowledge incidents <#add-acknowledgement-to-incidents>`_
      -  `Add ticket to incidents <#add-ticket-url-to-incidents>`_
      -  `Remove ticket from
         incidents <#remove-ticket-url-from-incidents>`_

-  `Customize notifications <#customize-alarm-notifications-in-argus>`_

   -  `About components of notification
      profiles <#about-components-of-notification-profiles>`_
   -  `About the available notification
      media <#about-the-available-notification-media>`_
   -  `Access your notification
      settings <#access-your-notification-profiles>`_
   -  `Add notification profile <#add-new-notification-profile>`_
   -  `Edit notification
      profile <#edit-existing-notification-profile>`_
   -  `Disable notification profile <#disable-notification-profile>`_
   -  `Delete notification profile <#delete-notification-profile>`_

-  `Manage notification
   time <#manage-when-to-receive-notifications-in-argus>`_

   -  `What is a timeslot <#what-is-a-timeslot-in-argus>`_
   -  `What is a recurrence <#what-is-a-recurrence-in-argus>`_
   -  `Access your timeslots <#access-your-timeslots>`_
   -  `Add recurrence <#add-new-recurrence>`_
   -  `Edit recurrence <#edit-recurrence>`_
   -  `Delete recurrence <#delete-recurrence>`_
   -  `Add timeslot <#add-new-timeslot>`_
   -  `Edit timeslot <#edit-existing-timeslot>`_
   -  `Delete timeslot <#delete-timeslot>`_

-  `Manage contact details
   (destinations) <#manage-your-contact-details-destinations-in-argus>`_

   -  `Access your
      destinations <#access-your-destinations-in-settings>`_
   -  `Add destination <#add-new-destination-in-settings>`_
   -  `Edit destination <#edit-existing-destination-in-settings>`_
   -  `Delete destination <#delete-destination-in-settings>`_

-  `Log out <#log-out-from-argus>`_

What is Argus?
--------------

Argus is an *alert aggregator* designed for storing and managing alerts
from different monitoring systems at one place. Argus is created for
**ease of alarm management** and **customizable alarm notifications**.

Log into Argus
--------------

Argus supports several login mechanisms: \* *username-password login* \*
*federated login with OAuth 2.0*

Log in and start using Argus at **/login**.

Login using username and password
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Fill out *username* and *password*.

2. Press ``LOGIN``.

Login using OAuth 2.0 (Feide in the example below)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Press ``LOGIN WITH OAUTH2``.

2. Select account you want to log in with.

3. Fill out *username* and *password* and press ``Log in``.

4. Continue with the preferred method for two-factor authentication.

Debugging Network errors on Login
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you get a following error message at the top of the *Login* page:

1. Open *developer console* in your browser.
2. Check the error message in the console.

   -  *Connection refused* error message indicates that the Argus API
      server is unavailable.
   -  *CORS* error message indicates misconfiguration of the Argus
      settings.

Please visit `Argus
documentation <https://argus-server.readthedocs.io/en/latest/index.html>`_
if you need help with the configuration.

Note that we intend to direct you to the browser’s developer console for
a specific error message in the case of network errors. This is due to
the fact that some network requests are meant to be delegated to
browsers, not the web applications (f.e. `preflight
requests <https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request>`_).

Work with alarms in Argus
-------------------------

**View**, **filter** and **update** alarms that come to Argus from
different sources (monitoring systems).

You can see all of your monitoring systems that are connected to Argus
in the *Sources selector*. Click on the *Sources selector* and all
available monitoring systems will appear in the drop-down menu.

What is an incident in Argus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An incident is an alarm that was sent to Argus from a monitoring system
of your choice.

Each incident has a *description* (created by the monitoring system),
*start time*, *duration*, *source* (which monitoring system it came
from), *tags* and *severity level*. An incident may have *end time*,
*ticket url* (associated ticket in an external ticket system). Incidents
may have different status. For example, an incident may be *open*, or
*closed* (resolved). An incident may also be *acknowledged* (noticed or
commented in any way), or not. In the detailed incident view below you
can get familiar with the above-mentioned attributes of an incident.
Note that an incident’s event feed is also available in the detailed
view. The event feed shows events like *closing* (resolving), and
*acknowledgment* of an incident.

Each row in the *Incidents* table is one alarm. In the table you can see
an incident’s *start time*, *closed/open status*, whether an incident
has at least one *acknowledgement*, *severity level*, *source* (which
monitoring system the incident came from), *description* (created by the
monitoring system) and whether the incident has an associated *ticket
url* (label icon at the very end of the row).

Access detailed incident view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Alternative 1:

   1. Click on an incident row in the *Incidents* table.

   2. Detailed incident will appear in a pop-up window.

-  Alternative 2:

   1. Click on one of the icons under *Actions column* in the
      *Incidents* table.

   2. App will redirect you to the incident’s page.

Work with incidents table
~~~~~~~~~~~~~~~~~~~~~~~~~

Change how many rows are shown per incidents table page
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Scroll down to the bottom of the *Incidents* table.

2. Click on the *Rows per page* drop-down.

3. Select whether you want 10/25/50/100 incidents per page displayed.

Navigate incidents table
^^^^^^^^^^^^^^^^^^^^^^^^

1. Scroll down to the bottom of the *Incidents* table.

2. Click on the *right arrow icon* if you want to go to the next table
   page.

3. Click on the *left arrow icon* if you want to go to the previous
   table page.

Change how often incidents table gets refreshed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Click on the *gears icon* to the right below the header.

2. Select refresh method in the *Auto Update selector*:

   -  If you want **no automatic table updates**, press ``NEVER`` in the
      *Auto Update selector*. Note that you will have to refresh the
      page yourself if you want the table to get updated.

   -  If you want the table to update **in realtime**, press
      ``REALTIME`` in the *Auto Update selector*.

   -  If you want the table to get updated **every couple of seconds**,
      press ``INTERVAL`` in the *Auto Update selector*.

      -  You can see the value of the current refresh interval below the
         *Incidents table*. The refresh interval is displayed **in whole
         seconds**.

      -  You can change the refresh interval value in
         ``/src/config.tsx``. The refresh interval is stored **in whole
         seconds**.

Decide which incidents are shown in the table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For ease of alarm management you can filter incidents so that only
incidents that match all preferred parameters are shown in the
*Incidents* table.

Apply the preferred filter by using the *Filter toolbar*. Argus will
remember your filter settings from the last login session, and will use
those until you change them.

*Filter toolbar* is available: \* Below the header in full-screen view.

-  In the *Filter Options dropdown* in mobile view.

Filter by open/close status
^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  If you only want *open* incidents to be displayed in the table, press
   ``OPEN`` in the *Open State selector*.

-  If you only want *closed* (resolved) incidents to be displayed in the
   table, press ``CLOSED`` in the *Open State selector*.

-  If you want both *open* and *closed* (resolved) incidents to be
   displayed in the table, press ``BOTH`` in the *Open State selector*.

Filter by acknowledgement status
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  If you only want *acknowledged* incidents to be displayed in the
   table, press ``ACKED`` in the *Acked selector*.

-  If you only want **un**\ *\ acknowledged* incidents to be displayed
   in the table, press ``UNACKED`` in the *Acked selector*.

-  If you want both *acknowledged* and *unacknowledged* incidents to be
   displayed in the table, press ``BOTH`` in the *Acked selector*.

Filter by source monitoring system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  If you want the table to display only incidents that came from a
   **specific monitoring system(s)**:

   1. Click on the *Sources input field*.

   2. In the drop-down that appears, you can see all available source
      systems. Click on the preferred one.

   3. Press *Enter*. The newly selected *source system* will appear in
      the input field.

   4. Repeat the process if you want to filter by several monitoring
      systems.

-  If you want the table to display incidents from **any monitoring
   system**, leave the *Sources field* empty.

Filter by tags
^^^^^^^^^^^^^^

-  If you want the table to display only incidents that have a
   **specific tag(s)**:

   1. Type in a *tag* into the *Tags input field* in the format
      ``tag_name=tag_value``.

   2. Press *Enter*. The newly added tag will appear in the input field.

   3. Repeat the process if you want to filter by several tags.

-  If you want the table to display incidents with **any tags**, leave
   the *Tags field* empty.

Filter by severity level
^^^^^^^^^^^^^^^^^^^^^^^^

The severity level ranges from *1 - Critical* to *5 - Information*. If
you select *max severity level* to be **5**, all incidents will be
displayed in the table. If you select *max severity level* to be **2**,
only incidents with severity **1** and **2** will be displayed in the
table.

To change *max severity level*: 1. Open the *Max severity level*
drop-down.

2. Select the preferred *max severity* option.

Filter out older incidents
^^^^^^^^^^^^^^^^^^^^^^^^^^

Note that you can not save this parameter in `stored
filters <#work-with-stored-filters>`_. 1. Click on the *gears icon* to
the right below the header.

2. Open the *Timeframe* drop-down menu.

3. Select the preferred option of *report-time-not-later-than* for the
   incidents in the table.

Work with stored filters
~~~~~~~~~~~~~~~~~~~~~~~~

After you `have set the preferred filter parameters for
incidents <#decide-which-incidents-are-shown-in-the-table>`_, you can
save your preferences as a *filter*. Stored *filters* can be used when
`customizing alarm
notifications <#customize-alarm-notifications-in-argus>`_.

Save current filter
^^^^^^^^^^^^^^^^^^^

1. `Set the preferred filter
   parameters <#decide-which-incidents-are-shown-in-the-table>`_.

2. Click on the *plus icon* within the *Filter input field*.

3. Give a (meaningful) name to your filter. Press ``CREATE``. Note that
   you can not edit a filter’s name after it is created.

Modify existing filter
^^^^^^^^^^^^^^^^^^^^^^

1. `Make desired changes to filter
   parameters <#decide-which-incidents-are-shown-in-the-table>`_.

2. Click on the *save icon* within the *Filter input field*.

3. Click on the filter that you want to update, and press ``SAVE TO``.

Apply existing filter
^^^^^^^^^^^^^^^^^^^^^

1. Click on the *Filter input field*.

2. Click on the preferred filter in the drop-down menu.

Unselect applied filter
^^^^^^^^^^^^^^^^^^^^^^^

1. Click on the *cross icon* inside the *Filter input field*.

Delete existing filter
^^^^^^^^^^^^^^^^^^^^^^

1. Click on the *gears icon* inside the *Filter input field*.

2. Select which filter you want to delete by clicking on the *bin icon*.

3. Confirm deletion.

Update one incident
~~~~~~~~~~~~~~~~~~~

Re-open a closed (resolved) incident
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. `Open incident in detailed view <#access-detailed-incident-view>`_.

2. Press ``OPEN INCIDENT``.

3. Confirm re-opening.

Close (resolve) an incident
^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. `Open incident in detailed view <#access-detailed-incident-view>`_.

2. Press ``CLOSE INCIDENT``.

3. Press ``CLOSE NOW``. Note that you can provide a closing comment if
   needed.

Add acknowledgement to an incident
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. `Open incident in detailed view <#access-detailed-incident-view>`_.

2. Press ``CREATE ACKNOWLEDGEMENT``.

3. Press ``SUBMIT``. Note that you can optionally provide an
   acknowledgement comment and/or a date when this acknowledgement is no
   longer relevant.

Update incident ticket
^^^^^^^^^^^^^^^^^^^^^^

Manually add ticket URL to an incident
''''''''''''''''''''''''''''''''''''''

1. `Open incident in detailed view <#access-detailed-incident-view>`_.

2. Type/paste in ticket URL into the *Ticket input field*. Note that the
   URL has to be absolute (full website address).

3. Press ``SAVE TICKET URL``.

Edit ticket URL
'''''''''''''''

1. `Open incident in detailed view <#access-detailed-incident-view>`_.
2. Press ``EDIT TICKET URL``.

3. Type/paste in ticket URL into the *Ticket input field* and press
   ``SAVE TICKET URL``. Note that the URL has to be absolute (full
   website address).

Remove ticket URL from an incident
''''''''''''''''''''''''''''''''''

1. `Open incident in detailed view <#access-detailed-incident-view>`_.
2. Press ``EDIT TICKET URL``.

3. Remove URL from the *Ticket input field* and press
   ``SAVE TICKET URL``.

Automatically generate ticket
'''''''''''''''''''''''''''''

Argus supports automatic ticket generation from the incident. This
feature needs additional configuration. Read more in the `Argus
documentation for ticket
systems <https://argus-server.readthedocs.io/en/latest/ticket-systems.html>`_.

1. `Open incident in detailed view <#access-detailed-incident-view>`_.

2. Press ``CREATE TICKET``.

3. Confirm automatic ticket generation.

4. When ticket is successfully generated, the *Ticket input field* is
   updated with a new ticket URL, and the ticket itself is opened in a
   new browser tab.

Please, check that your ticket system configuration in Argus is complete
if you get a following error message:

You can read more about ticket system settings
`here <https://argus-server.readthedocs.io/en/latest/ticket-systems/settings.html>`_.

Update several incidents at a time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Re-open closed (resolved) incidents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Select several incidents in the *Incidents table* and press
   ``RE-OPEN SELECTED`` in the *table toolbar*.

2. Confirm re-opening.

Close (resolve) incidents
^^^^^^^^^^^^^^^^^^^^^^^^^

1. Select several incidents in the *Incidents table* and press
   ``CLOSE SELECTED`` in the *table toolbar*.

2. Press ``CLOSE NOW``. Note that you can provide a closing comment if
   needed.

Add acknowledgement to incidents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Select several incidents in the *Incidents table* and press ``ACK``
   in the *table toolbar*.

2. Press ``SUBMIT``. Note that you can optionally provide an
   acknowledgement comment and/or a date when these acknowledgements are
   no longer relevant.

Add ticket URL to incidents
^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Select several incidents in the *Incidents table* and press
   ``ADD TICKET`` in the *table toolbar*.

2. Type/paste in ticket URL into the *Valid ticket URL field* and press
   ``SUBMIT``. Note that the URL has to be absolute (full website
   address).

Edit ticket URL for several incidents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Same process as `adding ticket URL to
incidents <#add-ticket-url-to-incidents>`_.

Remove ticket URL from incidents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Select several incidents in the *Incidents table* and press
   ``ADD TICKET`` in the *table toolbar*.

2. Leave the *Valid ticket URL field* empty and press ``SUBMIT``.

Customize alarm notifications in Argus
--------------------------------------

Choose **when**, **where** and **what** alarm notifications you want to
receive by creating, editing and deleting *notification profiles*.

About components of notification profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Timeslot** allows you to customize **when** you want to receive the
   alarm notifications. You can choose one timeslot per notification
   profile. Timeslots are reusable across multiple notification
   profiles.
2. **Filter** allows you to customize **what** alarms (incidents) you
   want to receive the notifications about. You can choose multiple
   filters per notification profile. Filters are reusable across
   multiple notification profiles.
3. **Destination** allows you to customize **where** you want to receive
   the alarm notifications. You can choose multiple destinations per
   notification profile. Destinations are reusable across multiple
   notification profiles. Destinations may be of `different media
   types <#about-the-available-notification-media>`_.

About the available notification media
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The notification media that are available in Argus by default are: - SMS
- Email

If you wish to receive notifications to other media, read about
configurable media types in the `Argus documentation for notification
plugins <https://argus-server.readthedocs.io/en/latest/notifications.html#other-notification-plugins>`_.

Access your notification profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Press ``PROFILES`` in the header.

Add new notification profile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. `Go to your notification
   profiles <#access-your-notification-profiles>`_.
2. Click on the ``CREATE NEW PROFILE`` button.

3. Select a timeslot for when to receive notifications in the *Timeslot
   drop-down*. If the drop-down menu is empty, `create a
   timeslot <#add-new-timeslot>`_ first.

4. Select what alarms you want to receive notifications about in the
   *Filters drop-down*. If the drop-down menu is empty, `create a
   filter <#save-current-filter>`_ first. Note that if no filter is
   selected no notification will be sent. You can select multiple
   filters per notification profile.

5. Select what destination(s) you want to receive notifications to in
   the *Destinations drop-down*. If the drop-down menu is empty, create
   a new destination by clicking on the *Plus* button first.

6. Press ``CREATE``.

Edit existing notification profile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. `Go to your notification
   profiles <#access-your-notification-profiles>`_.
2. Change a timeslot for when to receive notifications in the *Timeslot
   drop-down* (if needed).

3. Change what alarms you want to receive notifications about in the
   *Filters drop-down* (if needed).

4. Change what destinations(s) you want to receive notifications to in
   the *Destinations drop-down* (if needed).

5. Press ``SAVE``.

Disable notification profile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. `Go to your notification
   profiles <#access-your-notification-profiles>`_.
2. Uncheck the *Active checkbox* inside one of your existing
   notification profiles.

3. Press ``SAVE``.

Delete notification profile
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. `Go to your notification
   profiles <#access-your-notification-profiles>`_.
2. Press ``DELETE`` inside one of your existing notification profiles.

Manage when to receive notifications in Argus
---------------------------------------------

Add, edit or delete timeslots in *Timeslots*.

What is a timeslot in Argus
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A timeslot is a collection of one or more recurrences with a meaningful
name. Saved timeslots can be used when `customizing alarm
notifications <#customize-alarm-notifications-in-argus>`_. Each
timeslot represents a window (or several windows) of time for when it is
OK to receive alarm notifications.

Note that every user has the default timeslot *All the time*:

What is a recurrence in Argus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Recurrences are building blocks for timeslots. Each recurrence
represents a time range on selected weekdays for when it is OK to
receive alarm notifications. A time range can either be: \* a whole day,
\* or a window of time

Each recurrence has only one time range, and it applies to all days that
are selected in a given recurrence.

For example, in this timeslot with 3 recurrences, alarm notifications
are allowed from 4 p.m. to 8 a.m. on business days (note that it is not
possible to have a recurrence that goes from one day to the next), and
all hours on weekends:

Access your timeslots
~~~~~~~~~~~~~~~~~~~~~

1. Press ``TIMESLOTS`` in the header.

Add new recurrence
~~~~~~~~~~~~~~~~~~

Each timeslot has at least one recurrence by default. In the *Create New
Timeslot* box the default recurrence is from 8 a.m. to 4 p.m. on
business days. Add more recurrences if your timeslot needs more than
one. 1. `Go to your timeslots <#access-your-timeslots>`_. 2. Press
``ADD RECURRENCE`` either in the *Create New Timeslot* box, or in one of
your existing timeslots.

Edit recurrence
~~~~~~~~~~~~~~~

1. `Go to your timeslots <#access-your-timeslots>`_.
2. Modify one of the existing recurrences either in the *Create New
   Timeslot* box, or in one of your existing timeslots:

   -  If needed, change *start time* either by typing a new value or by
      using the calendar icon.

   -  If needed, change *end time* either by typing a new value or by
      using the calendar icon.

   -  Check *All day* if you want the recurrence to be from 00:00 a.m.
      to 11:59 p.m. Note that if *All day* is checked, you do not need
      to provide *start-* and *end time*.

   -  If needed, change day(s):

      1. Open drop-down menu.

      2. Select/de-select days for this recurrence by clicking on them
         once. Selected days are highlighted in light-yellow.

      3. Click away anywhere outside the drop-down menu.

Delete recurrence
~~~~~~~~~~~~~~~~~

1. `Go to your timeslots <#access-your-timeslots>`_.

2. Press ``REMOVE`` inside one of the existing recurrences either in the
   *Create New Timeslot* box, or inside one of your existing timeslots.

Add new timeslot
~~~~~~~~~~~~~~~~

1. `Go to your timeslots <#access-your-timeslots>`_.

2. Go to the *Create New Timeslot* box.

   -  In full-screen view it is visible by default at the top:

   -  In mobile-view press the button with the *pencil-icon* at the top
      to unfold the *Create New Timeslot* box:

3. Type in a (meaningful) timeslot name.

4. `Add another recurrence(s) <#add-new-recurrence>`_ if needed.

5. `Edit recurrence(s) <#edit-recurrence>`_ if needed.

6. `Remove recurrence(s) <#delete-recurrence>`_ if needed.

7. Press ``CREATE``.

8. The *Create New Timeslot* box will refresh to default and your newly
   created timeslot will appear at the bottom of the timeslot list. Note
   that existing timeslots have a dark border at the top.

Edit existing timeslot
~~~~~~~~~~~~~~~~~~~~~~

1. `Go to your timeslots <#access-your-timeslots>`_.

2. Modify one of your existing timeslots:

   -  Change the name if needed.

   -  `Add another recurrence(s) <#add-new-recurrence>`_ if needed.

   -  `Edit recurrence(s) <#edit-recurrence>`_ if needed.

   -  `Remove recurrence(s) <#delete-recurrence>`_ if needed.

3. Press ``SAVE``. Note that the ``SAVE``-button is inactive if no
   changes were made. The ``SAVE``-button is also inactive if some
   changes are invalid. In this case error messages inside the timeslot
   box will help you.

Delete timeslot
~~~~~~~~~~~~~~~

1. `Go to your timeslots <#access-your-timeslots>`_.

2. Press ``DELETE`` inside one of the existing timeslots. Note that the
   ``DELETE``-button is disabled in the *Create New Timeslot* box.

Manage your contact details (destinations) in Argus
---------------------------------------------------

Add, edit or delete contact details, aka destinations, in your settings.
Destinations that are present in your settings can be used when
`customizing alarm
notifications <#customize-alarm-notifications-in-argus>`_.

In Argus, *emails* and *phone numbers* are the destinations that are
configured by default. If you wish to receive notifications to other
media, read about configurable media types in the `Argus documentation
for notification
plugins <https://argus-server.readthedocs.io/en/latest/notifications.html#other-notification-plugins>`_.

Access your destinations in settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Click on the *user icon* in the header.

2. Click on ``Destinations`` in the drop-down menu.

Add new destination in settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. `Go to your contact
   details <#access-your-destinations-in-settings>`_.

2. Click on the *Plus* button in the *Destinations* header to open the
   *Create new destination* menu.

3. Select destination’s media type.

4. Type in a title (optional), and a destination value (required). Press
   ``CREATE``.

Edit existing destination in settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. `Go to your contact
   details <#access-your-destinations-in-settings>`_.

2. Modify one of the existing destinations.

3. Press ``SAVE``.

Delete destination in settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. `Go to your contact
   details <#access-your-destinations-in-settings>`_.

2. Press ``DELETE`` inside one of your saved destinations.

Note that some destinations are connected to your Argus user profile,
and can not be deleted. The ``DELETE`` button is disabled for such
destinations:

Log out from Argus
------------------

1. Click on the *user icon* in the header.

2. Click on ``Logout`` in the drop-down menu.
