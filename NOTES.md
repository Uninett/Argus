# Release Notes

This file documents changes to Argus that are relevant for operations,
customizers and end-users.

## [2.1.0] - 2025-06-30

One new user preference.

One new and one changed management command, both for better manipulation of
incidents via the CLI.

### Added

- Add a preference to change the incidents table layout to compact or standard
  ([#1399](https://github.com/Uninett/Argus/issues/1399))
- Add CLI command to close incidents
  ([#1450](https://github.com/Uninett/Argus/issues/1450))
- Add option to `create_fake_incident` to generate incidents from json files
  ([#1451](https://github.com/Uninett/Argus/issues/1451))

## [2.0.0] - 2025-05-26

This release completely removes version 1 of the API. If you have not done so,
please update your glue services and other integrations using API v1 to use
version 2!

We also archived the old frontend and dropped all support for it.

Please make sure to first migrate to the last release (1.37.0) before upgrading
to 2.0.0.

If you have used the HTMX frontend already and are using a local settings file
you should remove/comment out the lines

`update_settings(globals(), APP_SETTINGS)`

and

`ROOT_URLCONF = "argus.htmx.root_urls"`

and corresponding imports if you are getting the error

`django.core.exceptions.ImproperlyConfigured: Application labels aren't unique,
duplicates: django_htmx`.

### Removed

- Deleted API v1, its tests and mentions in the documentation. As well as all
  support for the old frontend. Any endpoint starting with "/api/v1" replies
  with "410 Gone". ([#1446](https://github.com/Uninett/Argus/pull/1446),
  [#1445](https://github.com/Uninett/Argus/pull/1445),
  [#1428](https://github.com/Uninett/Argus/pull/1428),
  [#1427](https://github.com/Uninett/Argus/pull/1427),
  [#1423](https://github.com/Uninett/Argus/pull/1423),
  [#1422](https://github.com/Uninett/Argus/pull/1422),
  [#1417](https://github.com/Uninett/Argus/pull/1417),
  [#1415](https://github.com/Uninett/Argus/pull/1415))

### Added

- Added an optional banner below the navbar that can be filled with text
  controlled via environment variable/Django setting.
  ([#1164](https://github.com/Uninett/Argus/issues/1164))


## [1.37.0] - 2025-05-14

This is the first release to not support any Django older than 5.2.

There's a very important future-proofing database schema change in this release.

The primary keys of the models Incident, Tag, IncidentTagRelation and Event
(and indirectly Acknowledgment) were changed from a 32-bit signed integer to
a 64-bit signed integer since these may grow for all eternity.

### How to check if you can migrate as usual

You can upgrade with a standard `python manage.py migrate` *iff* your database
is still small enough. You should probably test first. Make a *copy* of the
production database. If even making a copy takes forever you cannot migrate as
usual.

Migrate the *copy* while you time how long it takes. If it is quick enough
(less than a minute, say), you can migrate your production database as usual.
If it takes more than a single digit of minutes you should probably do it in
a maintenance window with the appropriate people notified in advance. If it
takes *hours* you should *not* use the included migration!

### What to do if you *can't* migrate as usual

Fake the migration. You do that by running

```
python manage.py migrate argus_incident 0009 --fake
```

This creates a single new row in the table `django_migrations` and should be
over in microseconds. After this, you can upgrade as usual later.

Your database might eventually run out of ids, depending on how many new
incidents are recorded per hour.

### How to migrate the hard and unusual way

Record the output of

```
python manage.py sqlmigrate argus_incident 0009
```

which is what the migration does to the database schema. Give that record to
your DBA.

We plan to add suggestions for how to migrate the hard way at a later date.

## [1.36.1] - 2025-04-23

The fallback setting of `EMAIL_USE_TLS` changed from a hardcoded `True` to
reading from an environment variable with a fallback to `False` in 1.36.0.
This broke at least one site that used the settings file
`argus.site.settings.base` directly and did not set `EMAIL_USE_TLS` explicitly.
This prevented the sending of emails.

We recommend setting `EMAIL_USE_TLS` explicitly in your own settings, either as
an environment variable (`"1"` for `True`, `"0"` for `False`) or directly in
a production settings file.

There was also a bug in the automatic creation of tickets in the new frontend
that should now be fixed.

## [1.36.0] - 2025-04-22

The new frontend is feature complete.

No development or support will be done on the *old* frontend from now on,
please switch to the new one ASAP.

## [1.35.0] - 2025-04-09

The new frontend is now just about on par feature-wise with the old frontend,
though we do not aim for bug compatibility =)

Feel free to switch over to the new frontend.

**Remember to migrate the database**

## [1.34.1] - 2025-03-26

Bugfix release, docker files should be able to run argus again.

## [1.34.0] - 2025-03-26

**This release marks the start of the process towards argus-server 2.0!**

API V2 is hereby declared stable, and V1 is hereby deprecated.

Version 2 will *drop support* for API V1 *and* the old frontend. Please try the
new frontend and send us some feedback!

The next Django LTS, 5.2, will not support any PostgreSQL older than version
14, so please upgrade ASAP.

The incident list in the new frontend is now feature complete. The timeslots
page has been prettified but also has some bugs. There's lots of remaining UX
things to do.

## [1.33.0] - 2025-03-05

Moved channels app from base settings to spa settings, where it belongs. This
avoids an ImportError on new installs.

Filtering by tags now possible in the new frontend.

## [1.32.0] - 2025-03-03

Mostly changes to the new frontend again, as well as some new and improved
docs.

If you use the old frontend and have a heavily customized settings-file, make
sure it is compatible with the settings in `argus.spa.settings`, as the spa-app
is no longer included by default in `INSTALLED_APPS`. For the same reason,
running `redis` is only necessary if using the spa settings.

With the new frontend, visiting the root of the site will now redirect to the
incidents list and therefore possibly triggering a log in.

## [1.31.0] - 2025-01-17

Mostly changes to the new frontend this time around.

Two development-relevant changes that affect customization:

- Refactor of incident-specific frontend pages, many files have new names
- How to define a preference has changed

There are visible changes to the destinations-page and profiles page as well.

This release is the first round of polish for the profiles page. More is to
come.

## [1.30.0] - 2024-12-19

Final release of the year! This was again mostly changes to the alpha frontend.

This release adds support for showing, adding, changing and deleting timeslots
and notificaton profiles, though with no graphical polish whatsoever.

The only functionality that is still to be finished is in the filter box on the
incidents page:

* filtering on tags
* loading and saving filters

## [1.29.0] - 2024-12-06

Mostly changes to the alpha frontend that will not be detailed here.

Support for multple API tokens per user has been added, via django-rest-knox.
For that reason, the old API endpoints for dealing with token authentication
has been deprecated, and new endpoints have been added to v2 of the API.

We've copied the linting rules from argus-htmx, so anything that have not been
merged yet might have to be updated to keep the linters happy.

### Deprecated

All v1 API endpoints for dealing with phone numbers have been deprecated.
Please see the v2 endpoints dealing with destinations instead.

## [1.28.0] - 2024-11-29

This version marks the inclusion of our new, alpha web frontend. It does not do
everything the existing standalone frontend does yet, hence alpha. See docs for
how to test.

## [1.27.0] - 2024-11-13

The big but hidden new feature this time is a new database table to hold user
preferences, in a namespaced fashion. Different apps can have different sets of
preferences with the same names but different values.

There is as of yet nothing that uses the preferences. The machinery needs to
be in place for the new frontend.

See the docs and remember to migrate.


## [1.26.1] - 2024-11-08

Bugfix release, logout via the React SPA frontend should now work again.

### Admin improvement

It is now possible to delete "dormant" users, defined as: users that have never
created an event or incident. Such users may be autocreated when testing new
login methods.

## [1.26.0] - 2024-10-29

This release is mainly to wrangle dependencies to the in-progress new frontend.

## [1.25.0] - 2024-10-24

There's a new library `argus.htmx` that exists to make it easier to develop the
new frontend. The new frontend cannot be run simultaneously with the REACT SPA
frontend as some settings conflict.

See the new docs in `docs/reference/htmx-frontend.rst` for details.

## [1.24.0] - 2024-10-22

### Deployment changes!

All the hard coded support for the REACT SPA frontend has been split out into
a library.

In the process, the following renames were done:

- `ARGUS_COOKIE_DOMAIN` -> `ARGUS_SPA_COOKIE_DOMAIN` (environment variable)
- `COOKIE_DOMAIN` -> `SPA_COOKIE_DOMAIN` (setting)
- `ARGUS_TOKEN_COOKIE_NAME` -> `ARGUS_SPA_TOKEN_COOKIE_NAME` (hidden setting)

How to deploy argus-server with support for this frontend has also changed, see
the new documentation section "REACT Frontend". In short, it is necessary to
change which settings-file to base the deployment on.

You might have to rebuild docker images: ours uses a newer Python (3.10) and
PostgreSQL (14) than they used to.

Any setting can now be changed via the (EXTRA|OVERRIDING)\_APPS-machinery.


## [1.23.0] - 2024-10-10

This is the first version of Argus to be able to run on Django 5.1.

Support for Python 3.8 has been dropped.

The most visible changes are in the documentation.

The function `get_psa_authentication_names()` has been remooved, it was not in
use by us.

How to customize filtering has changed, it is no longer necessary to override
`FilterSerializer` and `validate_jsonfilter`.

## [1.22.0] - 2024-08-30

There's a backwards incompatible change to prepare for the next Django LTS
(5.2): The setting `STATICFILES_STORAGE` has been replaced with `STORAGES`. If
`STATICFILES_STORAGE` has been changed from the provided default in
a deployment, it will have to be updated. See `STORAGES["staticfiles"]` in for
instance `argus.site.settings.base`.

Changing ticket urls in bulk now sends out change events, behaving like other
bulk changes. This means there will be an overall increase in events if bulk
changing tickets is common.

## [1.21.0] - 2024-08-20

The "description" field on Incident is now editable via API.

## [1.20.0] - 2024-07-25

This moved around *a lot* of code in order to allow swapping out the filtering
system. The Filter-model is still used but the bits that uses the contents of
Filter.filter is independent of the model.

## [1.19.2] - 2024-05-28

Optimization of API Incident PUT/PATCH.

## [1.19.1] - 2024-05-16

Tiny bugfix-release, nothing to see here.

## [1.19.0] - 2024-05-15

Remember to migrate!

*Backwards-incompatible change*: Because it is now possible to filter on
multiple event types instead of just one, both API V1 and API V2 has changed
its schema for Filter.filter.

* The key `"event_type"` is gone from V1. It never should have been there in
  the first place since it's new functionality.
* The key `"event_type"` has been *replaced* with a new key `"event_types"` in
  V2. Where `"event_type"` was a single string, `"event_types"` is a list of
  strings.

Luckily, the frontend at https://github.com/Uninett/argus-frontend never added
support for this feature.

Behavior does not change as the key not being set (or set to None/empty list)
will ignore the key when sending notifications.

Existing instances of `"event_type"` in the database is automatically changed
to `"event_types"` iff `"event_type"` was not falsey. Reversing the migration
will set `"event_type"` to the first string in `"event_types"` hence might lose
data: *don't reverse the migration in production!*

## [1.18.0] - 2024-05-07

There's a new API endpoint allowing the deletion of an existing incident and
its events. The new setting `INDELIBLE_INCIDENTS` controls this, the backwards
compatible setting is `True`. Toggle to `False` to allow deletion. The plan
forward is to limit deletion according to some rule we haven't decided on:

* limit it to "new" incidents, for an unfinished definition of "new"
* have an (optional) flag on incident controllable by the source
* so.. many.. ideas, hence, running code now, hard decisions later.

Smaller change: the data in Incident.metadata can now be replaced with HTTP
PATCH/PUT, in line with `ticket_url`, `details_url` and `level`.

## [1.17.0] - 2024-05-03

This release marks the start of The Great HTMx Experiment and a cooperation
with Geant.

Incidents have a gotten a new field so remember to run migrations.

There's a new "How To"-section in the docs, we expect it to grow rapidly.

There's lots of quality of life improvements in the admin.

There's a new way to add additional django apps to your own instance of
argus-server. Currently this is only via two new environment variables, see the
settings-documentation.

## [1.16.0] - 2024-04-23

The official docker image has been changed so if you use it in production have
a peak first.

The stresstest command is now a lot more useful: it is handy for even more
lazily creating a lot of fake incidents in the database where you don't care
about he contents. Just remember to turn off sending of notifications first!
You can turn it of or on for specific profiles with a new cli command:
`toggle_profile_activation`. It is now also easier to toggle, activate and
deactivate profiles in the admin. Have a look.

`django-debug-toolbar` has been added as a dev dependency but it is not in use
in the included dev settings yet.

## [1.15.0] - 2024-04-10

This release finishes the process started in 1.14.3. Make sure to run
the migrations in 1.14.3 before you run the migrations included here!

Furthermore, Django 3.2 is no longer supported so upgrade, upgrade!

## [1.14.3] - 2024-04-09

This release changes the database in order to get rid of a dead dependency,
make sure to run migrations:

```console
$ python manage.py migrate
```

This version can run on Django 5.0 if necessary. Install the dependencies in
`requirements-django50.txt` if so.

## [1.14.2] - 2024-02-15

This version can run on Django 4.2. In production, ensure that the list of
entries in `CSRF_TRUSTED_ORIGINS` are absolute urls, all starting with
`https://`.

The CHANGELOG is now maintained by `towncrier`.

The frozen requirements-files have been updated with new versions, please
upgrade which versions are used in production accordingly with
`pip install -r requirements-djangoVERSION.txt` where VERSION is either `32`for
Django 3.2 or `42` for Django 4.2.

## [1.14.1 - 2023-12-05]

### Changed

- Restructured documentation about integrations

## [1.14.0] - 2023-01-03

Due to a change in the signature of `NotificationPlugin.send()`, 3rd party
plugins will need to mark better which versions of argus-server they work with
in their dependencies-list. The old-style plugins work on 1.9-1.13.

### Added
- Add the "installed" field to the media serializer. This is so that the
  frontend can detect media used that is no longer installed on the backend.

### Fixed
- Ensure the right notifications go to the right destinations when sending many
  of each.

### Changed
- Change the signature of the notification-plugin `send`-method to avoid
  passing in the database
- Send one email per email-address so as to not leak who else gets that email.

## [1.13.0] - 2023-09-19

Works with argus-frontend 1.11 and newer.

### Added
- Add inline destinations to user edit page in admin
- Add management command for listing filters
- Add management command for bulk acting on incidents matching a given filter

### Fixed
- Raise validation error on posting incident with tags without tag key

### Changed
- Drop support for Python 3.7
- Remove all remaining uses of `Filter.filter_string`, replace with
  Filter.filter, in preparation of removing the actual `filter_string` field
  from the database.

  The API v1 still accepts `filter_string` but it is optional. It will prefer
  the data in `filter`. v2 ignores the presence or absence of `filter_string`
  entirely.

## [1.12.4] - 2023-09-04

### Changed
- Ensure that the start event is created *after* the incident has its tags so
  that notification filters with tags trigger correctly.

## [1.12.3] - 2023-08-31

### Changed
- Change what is logged on notification sending in order to ease solving
  problems in production. Prior to this, we couldn't know whether there is
  a problem with matching an event to filters, or whether the problem is
  actually storing all incoming events. Turn on debug-logging to get it all.

## [1.12.2] - 2023-06-27

### Fixed
- When sending a notification in production a typo lead to an exception that
  prevented sending the notification but was otherwise hidden from the end
  user.

## [1.12.1] - 2023-05-05

### Fixed
- Fixed acking-bug that only occured if notifications were turned on

## [1.12.0] - 2023-05-03

### Added
- Add docs for how to write a notification plugin
- Add a new command "stresstest", for stress-testing the API
- Migration! Add a field "installed" to the Media-model
- Support running on Django 4.2
- Documented how to use email to send notifications to Slack
- Make the auth-method endpoint also show username/password

### Fixed
- Allow updating of a timeslot with an empty time recurrence list, which
  results in all time recurrences to be removed from the timeslot

### Changed
- Optimize and refactor bulk api operations
- Start the process of getting rid of `Filter.filter_string` by ensuring the
  info in `filter_string` is also in `Filter.filter`

## [1.11.1] - 2023-02-16

### Fixed
- CORS-headers do not want explicit port numbers if the ports are the default
  for their type, that is: 80 for http or 443 for https. This lead to CORS not
  working if there was an explicit port in the `ARGUS_FRONTEND_URL` setting,
  which used to generate a CORS entry for the frontend. Such port numbers are
  now stripped when generating the CORS header.

## [1.11.0] - 2023-02-02

With this version, the API for bulk changes of incidents and sending of
notifications to new and interesting destinations via destination plugins has
been frozen, and should be ready for use, completing what was started in 1.10.

### Added
- Also include frontend-url to incident in incident-serializer
- Show installed plugins in the metadata view

### Fixed
- Fix API for adding events in bulk, with tests
- Fix API for bulk acking, with tests

## [1.10.2] - 2022-12-13

### Changed
- Renamed the ticket creation endpoint via plugin from `/ticket/` to `/automatic-ticket/`

## [1.10.1] - 2022-12-08

### Changed

- Send serialized incidents to the ticket-plugin, not database objects
  (This makes plugins much easier to test.)

## [1.10.0] - 2022-11-17

### Added
- Added support for testing on Python 3.11 and Django 4.0, 4.1
- Plugin system for ticket system integrations, documented in the new "Ticket
  system settings" sections.
- Add a production-oriented Dockerfile and use Github to build and store images
- New API endpoint to create a new ticket in an external ticket system
- Add docs about notification plugins
- Added the possibility to filter notifications by event-type
- Added a management command that will create incidents if a source token is
  close to expiring
- Added an endpoint to create events for incidents in bulk
- Added an endpoint to set ticket_url of incidents in bulk
- Added the possibility to filter notifications by event-type

### Changed

- Flatten the json structure for posting acknowledgements.

## [1.9.0] - 2022-11-08

### Added

- Added an endpoint to acknowledge incidents in bulk
- Added an endpoint to get a refreshed auth token.
- Add a filter to find incidents with a duration longer than a given amount of
  minutes.
- Added tests for previously untested incident endpoints

## [1.8.1] - 2022-10-28

### Fixed
- Fix typo that prevented SMS messages from being sent.

## [1.8.0] - 2022-10-06

### Added
- A notification profile can now have a name.
- Added endpoint that returns True if another user has a destination with the
  same medium and settings as the destination with the given primary key

### Changed

- One timeslot can now be used by multiple notification profiles.

### Steps for upgrading

This update includes changes to the database model, requiring a migration of
the database.

## [1.7.0] - 2022-10-04

### Added

- Documentation for our own management commands (CLI-scripts)

### Steps for upgrading

Running migrate will complete the changes that started with 1.6.0.

## [1.6.0] - 2022-10-04

### Added
- New API endpoint `/incidents/all-events/` for listing all events.
- Users can now have multiple emails and phone numbers

### Steps for upgrading

This update includes changes to the database model, requiring a migration of
the database.

Which notification plugins are in use are now decided by the new setting
`MEDIA_PLUGINS`. There are no default contents of this setting, to make it
possible to turn off notifications.

In order to support the included email and sms-plugins, add the following to
your tailored settings-file:


```
MEDIA_PLUGINS = [
    "argus.notificationprofile.media.email.EmailNotification",
    "argus.notificationprofile.media.sms_as_email.SMSNotification",
]
```

## [1.5.1] - 2022-05-03

### Fixed
- Acking an incident when notifications were turned on was broken, this is
  a workaround.

## [1.5.0] - 2022-05-03

### Added
- New query parameter `search` for the incident endpoint. This allows searching
  for incidents that contain given keywords. The result is a list of incidents
  where each given keyword exists in the incident description and/or in any
  event descriptions that belongs to the incident.
- External authentication supported via REMOTE_USER environment variable.

### Changed
- All mentions of Uninett has been replaced with Sikt. This is because Uninett
  was a merged into Sikt – Norwegian Agency for Shared Services in Education
  and Research on January 1st 2022.

### Steps for upgrading

This update includes changes to the database model, requiring a migration of
the database.

Note that the migration that allows the text-search is quite heavy and may time
out if you have very many incidents. If this happens, make an issue of it
(including how many incidents and how long it took before timing out) and we'll
make a patch-release with a documented work around for you.

### Steps for testing

In order to run tox successfully on Python 3.10, make sure tox was installed
with Python 3.10 or testing might fail with:

```
KeyError: scripts
```

## [1.4.0] - 2022-04-28

### Added
- New API endpoint `/login-endpoints/` for listing all login endpoints.
- New query parameter `count` for the incident endpoint to be used along with
  a filter. This will make the endpoint return a count of how many incident
  matches the given filter along with the filter itself. This is useful for
  debugging.
- The `level` attribute for incidents can now be updated via the incident
  endpoint.

### Changed
- The initial event for stateless incidents will now be labeled as "Stateless"
  instead of "Incident start". Stateful incidents are still labeled "Incident
  start".

### Steps for upgrading

This update includes changes to the database model, requiring a migration of
the database.

## [1.3.6] - 2022-04-21

### Fixed
- NotificationProfileViewV1 should no longer appear in API v2.
