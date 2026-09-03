Added management command to find the latest event from sources that does
not have `last_seen` set. Such sources might have been removed from
production, something might be wrong with them like using an outdated
API endpoint, or they were never put into production in the first place.
