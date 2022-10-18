# Release Notes
This file documents changes to Argus that are relevant for the users to know.

## [Unreleased]

## ticket-plugin-base

### Added
- Plugin system for ticket system integrations, documented in the new "Ticket
  system settings" sections.
- New API endpoint to create a new ticket in an external ticket system


### Added
- Add docs about notification plugins
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
