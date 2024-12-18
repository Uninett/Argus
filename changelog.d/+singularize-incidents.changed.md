Htmx: Customizers beware: Major refactor in src/argus/htmx/incident(s) and
src/argus/htmx/templates/htmx/incident(s).

* All directories named "incidents" was changed to "incident".
* The templates that defines columns in the incident list was moved to
  `htmx/incident/cells/`.
* The template for selecting sources in the filterbox was moved to
  `htmx/incident/widgets/`.
* Whenever there were plural view-names or url-names for incident-related views
  they were made singular.
