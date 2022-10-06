# Release Notes
This file documents changes to Argus that are relevant for the users to know.

## [Unreleased]

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
