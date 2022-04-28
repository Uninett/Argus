# Changes
This file documents all changes to Argus. This file is primarily meant to be read by developers.

## [Unreleased]

### Added
- (PR #345) Add endpoint to incident API for counting results of a filter.
- (PR #319) Allow updating level attribute for incidents.
- (PR #348) Add support for python 3.10.
- (PR #352) Add new event type "LES".
- (PR #358) Add new API endpoint for listing all login endpoints.
- (PR #366) Support external authentication via REMOTE_USER environment variable.
- (PR #362) Add feature for searching through incident and event descriptions.
- (PR #333) Add support for multiple emails and phone numbers per user.
- (PR #365) Add endpoint for getting all events.

### Changed
- (94a26d5) Upgrade from django 3.2.11 to 3.2.12.
- (PR #369) Update README documentation for using create_fake_incident.
- (PR #370) Allow any length for event type keys instead of limiting it to
 a lenght of 3.
- (PR #364) Replace references to Uninett with Sikt.
- (PR #352) Make initial events for stateless incidents be of type "LES" instead of "STA".

### Removed
- (PR #358) Remove unsupported authentication backend.

### Fixed
- (14dccbb, 68ea69) Ensure unique source for incidents in incident queryset tests.

## [1.3.6] - 2022-04-21

### Added
- (354a997) Force djangorestframework dependency to be older than 3.13.

### Fixed
- (PR #331) Stop NotificationProfileViewV1 from appearing in API v2.
- (da49115) Fix signatures for ListFields.
