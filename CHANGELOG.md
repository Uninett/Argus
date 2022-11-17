# Changes
This file documents all changes to Argus. This file is primarily meant to be
read by developers.

## [Unreleased]

## ticket-plugin-base

### Added
- Plugin system for ticket system integrations, documented in the new "Ticket
  system settings" sections.
- New API endpoint to create a new ticket in an external ticket system


### Added

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
