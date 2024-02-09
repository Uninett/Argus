# Changes
This file documents all changes to Argus. This file is primarily meant to be
read by developers.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/Uninett/Argus/tree/master/changelog.d/>.

<!-- towncrier release notes start -->

### Added
- Added the possibility to filter incident by a given list of ids
- Add the "admin_url" field to the user serializer. This is so that the
  frontend can show a link to the Django admin.

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
