# Changes
This file documents all changes to Argus. This file is primarily meant to be
read by developers.

## [Unreleased]

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
