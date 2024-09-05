# Changes
This file documents all changes to Argus. This file is primarily meant to be
read by developers.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/Uninett/Argus/tree/master/changelog.d/>.

<!-- towncrier release notes start -->

## [1.22.1] - 2024-09-05


### Added

- Add method to get associated names of Incident levels
  ([#875](https://github.com/Uninett/Argus/issues/875))


## [1.22.0] - 2024-08-30


### Changed

- Refactored ticket creation code so the actual changing of the incident
  happens only in one place. Also moved the actual autocreation magic to
  utility functions (sans error-handling since that is response-type
  dependent). Made bulk changes of tickets actually create the ChangeEvents so
  that it behaves like other bulk actions and make it possible to get notified
  of changed ticket urls.
- Replace the setting `STATICFILES_STORAGE` with `STORAGES` to prepare for
  running on newer Djangos. See NOTES for details.

### Fixed

- Hopefully there will be fewer spurious test-failures thanks to explicitly
  creating the user connected to a sourcesystem. UniqueError, you won't be
  missd.
- Fixed broken link to dataporten authentication docs in README
  ([#broken-dataporten-link](https://github.com/Uninett/Argus/issues/broken-dataporten-link))
- Renamed 'docker-compose' to 'Docker Compose' in README
  ([#update-readme-command-naming](https://github.com/Uninett/Argus/issues/update-readme-command-naming))


## [1.21.0] - 2024-08-20


### Changed

- Make description editable
  ([#811](https://github.com/Uninett/Argus/issues/811))


## [1.20.1] - 2024-07-26

### Fixed

- `INCIDENT_LEVEL_CHOICES` was behaving oddly when debugging so it has been
  made a proper immutable constant.

## [1.20.0] - 2024-07-25


### Added

- Added method to check whether incident is acknowledged by a specific user
  group. ([#838](https://github.com/Uninett/Argus/issues/838))
- Made it possible to replace how Argus does filtering (for sending
  notifications and showing a list of incidents). See the howto "How to
  customize filtering".
- `OVERRIDING_APPS` and `EXTRA_APPS` now supports changing the
  MIDDLEWARE-setting. The key is "middleware" and the value is a dictionary of
  the dotted path of the middleware as the key, and an action as the value.
  Currently only the actions "start" and "end" is supported, putting the
  middleware at either the start of the list or the end, depending.

### Changed

BIG filter refactor/cleanup. All filter-stuff except the Filter-model has been
moved to a new app, argus.filter

- Move `Filter.filtered_incidents` to `argus.filter.queryset_filters.QuerySetFilter`
  - Change the signature so that it works on a filterblob, not a Filter model
    instance
- Ensure that the fallback filter, which is only relevant when sending
  notifications, is ignored everywhere else. First step in getting rid of this
  misfeature of a setting.
- Get rid of `NotificationProfile.filtered_incidents`, instead use
  `argus.filter.queryset_filters.QuerySetFilter.incidents_by_notificationprofile`
- Move Filter-dependent methods out of incident/models.py
- Move filter settings check to argus.filter
- Keep OpenAPI queryparam descriptions with their filters in argus.filter.filters
- Update and improve tests
- Move Filter `*_fits` methods to argus.filter.filterwrapper.FilterWrapper
- Move NotificationProfile `*_fits` methods to ComplexFilterWrapper
- Add docstring to argus.filter.filter
- Simplify/DRY existing filterwrapper methods, including tristate

### Fixed

- Removed one cause for spurious failures of tests
- Show infinite `end_time` as 'Still open' instead of datetime representation
  in email ([#793](https://github.com/Uninett/Argus/issues/793))
- Temporarily hide DestinationConfig from User admin in order to allow updating
  Users again. Undo if Django starts allowing JSONFields in UniqueConstraints.
  ([#822](https://github.com/Uninett/Argus/issues/822))
- Improve `/incident` endpoint response time by roughly 36% by pre-fetching
  incident tag data ([#837](https://github.com/Uninett/Argus/issues/837))


## [1.19.2] - 2024-05-28

### Added

- There is now a commented line in `argus.site.urls.urlpatterns` that if
  uncommented will allow logging into the API with username/password. This
  allows the use of the DRF HTML api to change records. This partially works
  with django-debug-toolbar and should ease some debugging sessions.

### Changed

- Optimized PUT/PATCH of incidents in API v2. Mainly by no longer replacing
  `Incident.search_text` on every Incident save, thereby avoiding looking up
  all events for that incident. The old behavior was fine when there was only
  a handful of events per incident but we can no longer assume that.

## [1.19.1] - 2024-05-16

### Fixed

- Fixed bug preventing naive printing of TimeRecurrences, triggering
  a traceback

## [1.19.0] - 2024-05-15

*Backwards-incompatible change*: Because it is now possible to filter on
multiple event types instead of just one, both API V1 and API V2 has changed
its schema for Filter.filter. See NOTES.md for details.

### Removed

- Removed `"event_type"` from the V1 Filter API, it should only have been
  available in V2 (since it was new) and it has never been in use by the
  frontend. ([#699](https://github.com/Uninett/Argus/issues/699))

### Added

- Add filtering of events by a list of event types
  ([#699](https://github.com/Uninett/Argus/issues/699))
- Add howto about how to set up and test federated login, using GitHub as an
  example. ([#803](https://github.com/Uninett/Argus/issues/803))
- Extend the usefulness of `OVERRIDE_APPS` and `EXTRA_APPS` by adding support
  for Django template engine context processors. Any context processors are
  added to the end of the list.
  ([#810](https://github.com/Uninett/Argus/issues/810))

### Changed

- Change how the description of a change event is formatted so that it is
  always consistent (not to mention DRY).
  ([#809](https://github.com/Uninett/Argus/issues/809))


## [1.18.0] - 2024-05-07


### Added

- New in the API: Allow sources to delete their own incidents, as well as allow
  superusers to delete any incident.
  ([#804](https://github.com/Uninett/Argus/issues/804))

### Changed

- Allow replacing Incident.metadata with another json blob via API, no
  questions asked, nothing to see here.
  ([#807](https://github.com/Uninett/Argus/issues/807))


## [1.17.0] - 2024-05-03


### Added

- Add a possibility to filter incidents by start time in incident admin list
  ([#739](https://github.com/Uninett/Argus/issues/739))
- Added an optional JSONField "metadata" to incident. This can be used for any
  additional info the glue-service would like to store on the incident that
  needs more structure than tags. The field has been added to the V2
  IncidentSerializer but we do not plan to expose it in the frontend.
- Added documentation on how to safely test notifications.
- Added simple support for pluggable django-apps. The setting `OVERRIDING_APPS`
  is loaded first in `INSTALLED_APPS` and `urls.py`, and can override templates
  and views. The setting `EXTRA_APPS` is safer, it is loaded last in
  `INSTALLED_APPS` and `urls.py` and can therefore only add additional
  templates and views.

### Changed

- When editing a notification profile in the admin UI, only the profile owner's
  own filters are now listed as available for selection.
  ([#735](https://github.com/Uninett/Argus/issues/735))
- Linked up the second column in the admin incident list to the details view in
  addition to the default first column because the first column is currently an
  optional field. If the field has no value there can also not be a link.
- Update the release checklist in `docs/` to current practices and turn it into
  a howto.

### Fixed

- Show fully qualified details URL in emails
  ([#744](https://github.com/Uninett/Argus/issues/744))
- Fix internal server error in timeslot admin due to removed method
  ([#797](https://github.com/Uninett/Argus/issues/797))


## [1.16.0] - 2024-04-23

### Added

- Added development dependency on django-debug-toolbar to make it easy to use.
- Adds more capability to the stresstest command, including incident creation
  verification, bulk ACKing and timeout configuration.
  ([#641](https://github.com/Uninett/Argus/issues/641))
- Add possibility to set fields when creating fake incidents in Django admin
  ([#669](https://github.com/Uninett/Argus/issues/669))
- Show user and filter by user in notification profile admin
  ([#734](https://github.com/Uninett/Argus/issues/734))
- Add cli command to toggle notification profile activation
  ([#747](https://github.com/Uninett/Argus/issues/747))
- Add admin action to change activation of profiles
  ([#748](https://github.com/Uninett/Argus/issues/748))
- Add API documentation for GET responses
  ([#752](https://github.com/Uninett/Argus/issues/752))
- Added an informational page on /, with favicon, in order to cut down on some
  common 404 log messages and set up the static files system properly.

### Changed

- Switched official Docker image to serve using gunicorn+uvicorn
  ([#766](https://github.com/Uninett/Argus/issues/766))
- Changed how tristates (open, acked, stateful) are logged in order to improve
  debuggability.
- Return False and log if sms-to-email has trouble with the email server.
- To improve debugability: Change how sending notifications are logged so that
  there's a log both when sending succeds and when it fails.

### Fixed

- Changed references to docs for Django 4.2
  ([#746](https://github.com/Uninett/Argus/issues/746))
- Do not allow used destinations to be deleted
  ([#753](https://github.com/Uninett/Argus/issues/753))
- Fix typo in admin that prevented sorting on incident id


## [1.15.0] - 2024-04-10

Due to the removal of the django-multiselectfield dependency it is vitally
important to upgrade to *this* version *after* correctly having upgraded to
1.14.3 (the previous version).

Be sure to migrate the database:

```console
$ python manage.py migrate
```

This version supports Django 4.2 and newer.

### Changed

- Drop all support for Django 3.2. No version-specific requirements for 3.2 are
  included anymore, and we no longer test on 3.2.

### Removed

- Remove django-multiselectfield dependency ([#707](https://github.com/Uninett/Argus/issues/707))

## [1.14.3] - 2024-04-09

This release changes the database in order to get rid of a dead dependency,
make sure to run migrations.

This version can run on Django 5.0 if necessary. Install the dependencies in
`requirements-django50.txt` if so.

This is the last version that supports Django 3.2.

### Added

- Add filtering of incident list by notificationprofile

  This returns all incidents that are included in filters that are connected to
  that notificationprofile
- Added support for running and testing on Django 5.0

### Changed

- Change TimeRecurrence.days from MultiSelectField to ArrayField
  ([#707](https://github.com/Uninett/Argus/issues/707))
- Updated lots of depenendcies in order to run on Django 5.0

## [1.14.2] - 2024-02-15

This version can run on Django 4.2. In production, ensure that the list of
entries in `CSRF_TRUSTED_ORIGINS` are absolute urls, all starting with
`https://`.

### Added

- Add filtering of incident list by filter

  This returns all incidents that are included in the filter
  ([#244](https://github.com/Uninett/Argus/issues/244))
- Allow running and testing on Python 3.12
- Added towncrier to automatically produce changelog
- Add two development dependencies

  While `tox` doesn't need to be in the venv, it DOES currently need to be less
  than version 4.

  `build` is useful for debugging pip errors and pip-compile trouble.
  Whenever pip-compile (via `tox -e upgrade-deps` for instance) fails with

  ```
  Backend subprocess exited when trying to invoke get_requires_for_build_wheel
  Failed to parse /PATH/pyproject.toml
  ```

  run `python -m build -w` to see what `build` is actually complaining about.

  See also https://github.com/pypa/build/issues/553
- Add the "admin_url" field to the user serializer. This is so that the
  frontend can show a link to the Django admin.
- Added the possibility to filter incident by a given list of ids

### Fixed

- Fixed posting/updating notification profiles without name

### Changed

- Updated a lot of (sub)dependencies to allow running on newer pythons and
  newer Djangos, and to quiet dependency bots

## [1.14.1 - 2023-12-05]

### Changed

- Restructured documentation about integrations

## [1.14.0] - 2023-01-03

Incomplete changelog.

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
- Log profile owners name when checking profiles
- Constrain subdependencies in a better way
- Send one email per email-address so as to not leak who else gets that email.
- Remove the `Filter.filter_string`-field from the database. We're not using it
  anymore and shouldn't ever use it by accident either.

## [1.13.0] - 2023-09-19

Works with argus-frontend 1.11 and newer.

### Added
- Lint for critical problems before testing in Github CI, to speed things up
- Added config-file for building docs at readthedocs
- Add inline destinations to user edit page in admin
- Add management command for listing filters
- Add management command for bulk acting on incidents matching a given filter

### Fixed
- Raise validation error on posting incident with tags without tag key

### Changed
- Update Django patch versions and various dependencies
- Drop support for Python 3.7. Github's CI/CD was sufficiently different from
  testing on local (different setuptools-version used maybe?) that we had
  a "fun" goose chase finding and upgrading the sub-dependency that broke the
  build.
- Remove all remaining uses of `Filter.filter_string`, replace with
  Filter.filter, in preparation of removing the actual `filter_string` field
  from the database.

  The API v1 still accepts `filter_string` but it is optional. It will prefer
  the data in `filter`. v2 ignores the presence or absence of `filter_string`
  entirely.

## [1.12.4] - 2023-09-04

### Changed
- Ensure that the start event is created *after* the incident has its tags so
  that notification filters with tags trigger correctly. The signal that
  creates the first event is gone, but the signal that triggers on creation of
  the first event is not, that will have to wait until we utilize a queue.

## [1.12.3] - 2023-08-31

### Changed
- Change what is logged on notification sending in order to ease solving
  problems in production

## [1.12.2] - 2023-06-27

### Fixed
- When sending a notification in production a typo lead to an exception that
  prevented sending the notification but was otherwise hidden from the end
  user.

## [1.12.1] - 2023-05-04

### Fixed
- Typo in code (that could have been found by flake8) lead to acks not working
  when notifications are turned on

## [1.12.0] - 2023-05-03

### Added
- More tests. Lots.
- Add docs for how to write a notification plugin
- Add a new command "stresstest", for stress-testing the API
- Start a process for revealing to the frontend which media plugins are
  actually installed
- Log a warning if a medium in the Media-table does not have a plugin installed
- Mention cookiecutter-template for tickets in the ticket docs
- Support running on Django 4.2
- Documented how to use email to send notifications to Slack
- Make the auth-method endpoint also show that username/password is supported
- In ticket-automation, show which fields were configured but not found in the
  generated ticket

### Fixed
- Lots of formatting-bugaboos in the docs
- Allow updating of a timeslot with an empty time recurrence list, which
  results in all time recurrences to be removed from the timeslot

### Changed
- Optimize and refactor bulk api operations
- Change how media plugins are accessed in order to avoid/control some exceptions
- Start the process of getting rid of `Filter.filter_string` by ensuring the
  info in `filter_string` is also in `Filter.filter`
- Correct some api examples in docs
- Only fork a new process to send notifications if there are any notifications
  to send
- Upgrade lots of dependencies
- Support explicit timestamp in `Incident.set_open/set_closed`
- Change how parameter names to SerializerMethodFields are set up
- Improved ticket docs
- Fixed typos
- Simplify generation of frozen dependency list: trust pyproject.toml

## [1.11.1] - 2023-02-16

### Added
- Coverage of the notificationprofile app was improved with several new tests

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

## Added
- Add default HTML template for autocreated tickets
- Also include frontend-url to incident in incident-serializer
- Output XML test-reports and set up github actions for it
- Show installed plugins in the metadata view

### Fixed
- Fix API for adding events in bulk, with tests
- Fix API for bulk acking, with tests

### Changed
- Improved OpenAPI by adding some more docstrings
- Updated version of github-actions actions
- Use better exceptions for ticket plugins
- Change how/where change-events are created
- Move tests for included destinations to individual files

## [1.10.2] - 2022-12-13

### Changed
- Renamed the ticket creation endpoint via plugin from `/ticket/` to `/automatic-ticket/`
- Refactored the view tests for NotificationProfile
- Explicitly set language in sphinx conf, silencing a warning

## [1.10.1] - 2022-12-08


## [1.10.1] - 2022-12-08


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
- Added an endpoint to set `ticket_url` of incidents in bulk
- Added an endpoint to create events for incidents in bulk

### Fixed
- Changed when the Media-table is synced with settings `MEDIA_PLUGINS` to avoid
  dev/prod-settings leaking into the tests

### Changed
- Flatten the json structure for posting acknowledgements.
- Improve Sonar Cloud settings, like just testing for Python 3

## [1.9.0] - 2022-11-08

### Added
- Add test for updating phone number in V1
- Add test for posting tag with invalid key
- Added an endpoint to acknowledge incidents in bulk
- Added an endpoint to get a refreshed auth token.
- Add a filter to find incidents with a duration longer than a given amount of
 minutes.
- Added tests for previously untested incident endpoints
- A Makefile that cleans away generated files

### Fixed
- Validate that user doesn't have destination with same settings before
  creating/updating destination
- Properly catch tag validtion errors
- The FilterFactory no longer leads to random UniqueViolations on testing

## [1.8.1] - 2022-10-28

### Fixed
- Fix typo that prevented SMS messages from being sent.

## [1.8.0] - 2022-10-06

### Added
- A notification profile can now have a name.
- Docstrings and type hints to functions of media plugins.
- Added tests for the email and sms destination serializer in case of invalid
  input for updating.
- Added tests for the incident, event and tag serializer
- Added endpoint that returns True if another user has a destination with the
  same medium and settings as the destination with the given primary key
- Add tests for filtering on stateful/statelss and open/closed incients.
- Add SMSNotification plugin to MEDIA_PLUGINS in development settings.

### Fixed
- Fix a notification profile test to include the phone number changes.
- Broken links and formatting in documentation.
- Fix notification profile serializer test to actually change phone number when
  updating.
- Make code snippets visible in release checklist in documentation.
- Validate tags before adding them to an incident
- Disallow the use of `argus` as username when creating admin user via the `initial_setup` script.

### Changed
- One timeslot can now be used by multiple notification profiles.
- Replaced wildcard imports with specific imports.
- Moved the notification profile Github test to parent folder and added
  regression tag.
- Renamed notification profile serializer tests to be more descriptive and
  added integration test tags.
- Improve query in notification profile signal test and add clarifying comment.
- Ran black again on whole code base.
- In media plugins rename the function `is_deletable` to
  `raise_if_not_deletable` and make it raise an error if a destination is not
  deletable.
- Split up and rename notification profile model tests

### Dependencies
- Upgrade from pyjwt 2.0.1 to 2.4.0
- Upgrade from django 3.2.13 to 3.2.15
- Upgrade from black 20.8b1 to 22.3.0 in pre-commit

## [1.7.0]

### Changed

- Clean away database tables rendered unnecessary due to changes in 1.6.0
- Modernize packaging. Package-building is all in pyproject.toml, tools are

### Changed

- Clean away database tables rendered unnecessary due to changes in 1.6.0
- Modernize packaging. Package-building is all in pyproject.toml, tools are
  configured either there or in tox.ini.

## [1.6.0] - 2022-10-04

### Added
- Add endpoint for getting all events.
- Add support for multiple emails and phone numbers per user.
- Allow source systems to post acknowledgements.
- Added clearer directions to the Argus documentation in the README.

### Fixed
- Rename the `media_v1` key in the notificationprofile endpoint back to `media`, as changing it to `media_v1` broke the frontend.
- Fix a notification profile test running duplicate asserts against one filter instead of actually testing the other defined filters.

### Changed
- Use more factories for notificationprofile tests.

## [1.5.1] - 2022-05-03

### Fixed
- Acknowledging incidents works again, thanks to a workaround.

## [1.5.0] - 2022-05-03

### Added
- Github actions: Add support for SonarQube (for Géant) and prevent CodeCov on
  3rd party forks
- Add feature for searching through incident and event descriptions.
- Support external authentication via REMOTE_USER environment variable.

### Changed
- Replace references to Uninett with Sikt.

### Dependencies
- Upgrade from django 3.2.12 to 3.2.13

## [1.4.0] - 2022-04-28

### Added
- Add new API endpoint for listing all login endpoints.
- Add new event type "LES" for stateless events.
- Add debugging endpoint to incident API for counting results of a filter.
- Allow changing level via incident endpoint

### Changed
- Make initial events for stateless incidents be of type "LES" instead of "STA".
- Update README documentation for using create_fake_incident.
- Allow any length for event type keys instead of limiting it to
 a lenght of 3.

### Fixed
- Ensure unique source for incidents in incident queryset tests.

### Removed
- Remove unsupported authentication backend.

### Dependencies
- Add support for python 3.10.
- Upgrade from django 3.2.11 to 3.2.12.

## [1.3.6] - 2022-04-21

### Fixed
- Stop NotificationProfileViewV1 from appearing in API v2.
- Fix signatures for ListFields.

### Dependencies
- Force djangorestframework dependency to be older than 3.13.
