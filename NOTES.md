# Release Notes
This file documents changes to Argus that are relevant for the users to know.

## [Unreleased]

### Added
- New API endpoint `/login-endpoints/` for listing all login endpoints.
- New API endpoint `/incidents/all-events/` for listing all events.
- New query parameter `search` for the incident endpoint.
This allows searching for incidents that contain given keywords.
The result is a list of incidents where each given keyword exists
in the incident description and/or in any event descriptions that belongs to the incident.
- New query parameter `count` for the incident endpoint to be used along with a filter.
This will make the endpoint return a count of how many incident matches the given filter
along with the filter itself.
- The `level` attribute for incidents can now be updated via the incident endpoint.
- External authentication supported via REMOTE_USER environment variable.
- Users can now have multiple emails and phone numbers

### Changed
- The initial event for stateless incidents will now be labeled as "Stateless" instead of "Incident start". Stateful incidents are still labeled "Incident start".
- All mentions of Uninett has been replaced with Sikt.

### Steps for upgrading

This update includes changes to the database model, requiring a migration of the database.
