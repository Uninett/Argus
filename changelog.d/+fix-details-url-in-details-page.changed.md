When showing the details url in the details page, use the generated absolute
url from the Incident.details_url and the Source.base_url. Validates that the
combination is valid and falls back to using the raw details url if not.
