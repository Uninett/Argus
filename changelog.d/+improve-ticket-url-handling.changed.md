Refactored ticket creation code so the actual changing of the incident happens
only in one place. Also moved the actual autocreation magic to utility
functions (sans error-handling since that is response-type dependent). Made
bulk changes of tickets actually create the ChangeEvents so that it behaves
like other bulk actions and make it possible to get notified of changed ticket
urls.
