# Release Notes
This file documents changes to Argus that are relevant for the users to know.

## [Unreleased]

### Changed
- Drop support for Python 3.7

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

## Added
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
