# Release Notes

## [1.?.?] - 2022-03-??

### New features
- New API endpoint `/login-endpoints/` for listing all login endpoints.
- New API endpoint `/incidents/all-events/` for listing all events.
- New query parameter `search` for the incident endpoint.
This allows searching for incidents that contain given keywords.
The result is a list of incidents where each given keyword exists
in the incident description and/or in any event descriptions that belongs to the incident.
- New query parameter `count` for the incident endpoint to be used along with a filter. This will make the endpoint return a count of how many incident matches the given filter along with the filter itself.
- The `level` attribute for incidents can now be updated via the incident endpoint.
- External authentication supported via REMOTE_USER environment variable.

### Changes
- The initial event for stateless incidents will now be labeled as "Stateless" instead of "Incident start". Stateful incidents are still labeled "Incident start".


### Steps for upgrading

This update includes changes to the database model, which means a migration is in order. This can be done via the `manage.py` tool with the command `python manage.py migrate`.

Django has been upgraded from 3.2.11 to 3.2.12

## [1.3.5] - 2022-01-24