# Changes

## [Unreleased]

### Added
- Stop NotificationProfileViewV1 from appearing in API v2. PR #331
- Force djangorestframework dependency to be older than 3.13.
- Fix signatures for ListFields.
- Add endpoint to incident API for counting results of a filter. PR #345
- Allow updating level attribute for incidents. PR #319
- Add support for python 3.10. PR #348
- Upgrade from django 3.2.11 to 3.2.12.
- Add new event type "LES". PR #352
- Make initial events for stateless incidents be of type "LES" instead of "STA". PR #352
- Add new API endpoint for listing all login endpoints. PR #358
- Remove unsupported authentication backend. PR #358
- Ensure unique source for incidents in incident queryset tests.
- Support external authentication via REMOTE_USER environment variable. PR #366
- Update README documentation for using create_fake_incident. PR #369
- Add feature for searching through incident and event descriptions. PR #362
- Add support for multiple emails and phone numbers per user. PR #333
- Allow any length for event type keys. PR #370
- Rebrand from Uninett to Sikt. PR #364
- Add endpoint for getting all events. PR #365
