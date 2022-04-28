# Changes
This file documents all changes to Argus. This file is primarily meant to be
read by developers.

## [Unreleased]

### Added
- Add endpoint to incident API for counting results of a filter.
- Allow updating level attribute for incidents.
- Add support for python 3.10.
- Add new event type "LES".
- Add new API endpoint for listing all login endpoints.
- Support external authentication via REMOTE_USER environment variable.
- Add feature for searching through incident and event descriptions.
- Add support for multiple emails and phone numbers per user.
- Add endpoint for getting all events.

### Changed
- Upgrade from django 3.2.11 to 3.2.12.
- Update README documentation for using create_fake_incident.
- Allow any length for event type keys instead of limiting it to
 a 3.
- Replace references to Uninett with Sikt.
- Make initial events for stateless incidents be of type "LES" instead of "STA".

### Removed
- Remove unsupported authentication backend.

### Fixed
- Ensure unique source for incidents in incident queryset tests.

## [1.3.6] - 2022-04-21

### Added
- Force djangorestframework dependency to be older than 3.13.

### Fixed
- Stop NotificationProfileViewV1 from appearing in API v2.
- Fix signatures for ListFields.
