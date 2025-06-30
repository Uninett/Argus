# Changes
This file documents all changes to Argus. This file is primarily meant to be
read by developers.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/Uninett/Argus/tree/master/changelog.d/>.

<!-- towncrier release notes start -->

## [2.1.0] - 2025-06-30

### Added

- Add a preference to change the incidents table layout to compact or standard
  ([#1399](https://github.com/Uninett/Argus/issues/1399))
- Add CLI command to close incidents
  ([#1450](https://github.com/Uninett/Argus/issues/1450))
- Add option to `create_fake_incident` to generate incidents from json files
  ([#1451](https://github.com/Uninett/Argus/issues/1451))

### Changed

- Use DRF's DEFAULT_PERMISSION_CLASSES setting for API endpoints' permission
  checking ([#1476](https://github.com/Uninett/Argus/issues/1476))
- Request is now passed to incident update actions to allow for sending
  messages ([#1497](https://github.com/Uninett/Argus/issues/1497))

### Fixed

- Ensure SourceSystemTypeFactory is called with lowercase name
  ([#1499](https://github.com/Uninett/Argus/issues/1499))
- Avoid trying to create incident with same source and source incident id
  ([#1500](https://github.com/Uninett/Argus/issues/1500))


## [2.0.1] - 2025-06-25

This release fixes a problem in the migrations shipped with 2.0.0. Only affects
development.

### Changed

- Fix fields incorrectly marked as autocreated in squashed migration
  ([#1506](https://github.com/Uninett/Argus/issues/1506))


## [2.0.0] - 2025-05-26

This release completely removes version 1 of the API. If you have not done so,
please update your glue services and other integrations using API v1 to use
version 2!

We also archived the old frontend and dropped all support for it.

Please make sure to first migrate to the last release (1.37.0) before upgrading
to 2.0.0.

If you have used the HTMX frontend already and are using a local settings file
you should remove/comment out the lines

`update_settings(globals(), APP_SETTINGS)`

and

`ROOT_URLCONF = "argus.htmx.root_urls"`

and corresponding imports if you are getting the error

`django.core.exceptions.ImproperlyConfigured: Application labels aren't unique,
duplicates: django_htmx`.

### Removed

- Deleted API v1, its tests and mentions in the documentation. As well as all
  support for the old frontend. Any endpoint starting with "/api/v1" replies
  with "410 Gone". ([#1446](https://github.com/Uninett/Argus/pull/1446),
  [#1445](https://github.com/Uninett/Argus/pull/1445),
  [#1428](https://github.com/Uninett/Argus/pull/1428),
  [#1427](https://github.com/Uninett/Argus/pull/1427),
  [#1423](https://github.com/Uninett/Argus/pull/1423),
  [#1422](https://github.com/Uninett/Argus/pull/1422),
  [#1417](https://github.com/Uninett/Argus/pull/1417),
  [#1415](https://github.com/Uninett/Argus/pull/1415))

### Added

- Added an optional banner below the navbar that can be filled with text
  controlled via environment variable/Django setting.
  ([#1164](https://github.com/Uninett/Argus/issues/1164))
- Added two new management commands: `createuser` and `changeuser`.
  ([#1449](https://github.com/Uninett/Argus/pull/1449))
- Added support for creating a source when calling `create_fake_incident` if
  the source does not exist.
  ([#1424](https://github.com/Uninett/Argus/issues/1424))
- Added option to set source type in `create_fake_incident` management command.
  ([#1486](https://github.com/Uninett/Argus/issues/1486))

### Changed

- Squashed existing migrations for the benefit of future changes in
  Argus v2. ([#1407](https://github.com/Uninett/Argus/issues/1407))
- Upgraded a lot of dependencies.
  ([#1485](https://github.com/Uninett/Argus/pull/1485))


## [1.37.0] - 2025-05-14

There's a very important change to the database schema in this release.
Depending on the amount of incidents in your database you might not be able to
migrate the normal way. Please see the [NOTES](./NOTES.md).

This is the first release to not support any Django older than 5.2.

### Added

- Add source argument to `create_fake_incident` CLI command

### Changed

- Drop support for all Django versions older than 5.2.
- The primary keys of the models Incident, Tag, IncidentTagRelation and Event
  (and indirectly Acknowledgment) were changed from a 32-bit signed integer to
  a 64-bit signed integer since these may grow for all eternity.


## [1.36.2] - 2025-04-29

### Changed, frontend

- Show better messages when handling errors when autocreating tickets.

## [1.36.1] - 2025-04-23

The fallback setting of `EMAIL_USE_TLS` changed from a hardcoded `True` to
reading from an environment variable with a fallback to `False` in 1.36.0.
This broke at least one site that used the settings file
`argus.site.settings.base` directly and did not set `EMAIL_USE_TLS` explicitly.
This prevented the sending of emails.

We recommend setting `EMAIL_USE_TLS` explicitly in your own settings, either as
an environment variable (`"1"` for `True`, `"0"` for `False`) or directly in
a production settings file.

### Changed

- The example production settings file (`argus.site.settings.prod`) now runs
  the new frontend and no longer supports the old frontend. In this
  settings-file, `EMAIL_USE_TLS` falls back to `True` if not set as an
  environment variable.
- Added "level"-filter for incidents in admin

### Frontend

#### Fixed

- Fixed autocreation of tickets


## [1.36.0] - 2025-04-22

The new frontend is feature complete.

No development or support will be done on the *old* frontend from now on,
please switch to the new one ASAP.

### Changed

- Update email settings to use port 25 by default, override defaults in prod.py
  ([#1395](https://github.com/Uninett/Argus/issues/1395))

### Frontend

#### Added

- Add font-awesome icon pack
  ([#1389](https://github.com/Uninett/Argus/issues/1389))
- Convert filterable column unicode search icon to fontawesome
  ([#1390](https://github.com/Uninett/Argus/issues/1390))
- Added new incident page filter parameter "timeframe" to be on par with the
  old frontend. This allows hiding older incidents by age. The chosen "ages"
  are hard-coded, as it was in the old frontend.

#### Changed

- Made styling of the elements in the footer more blended in.
  ([#1363](https://github.com/Uninett/Argus/issues/1363))
- Made select dropdowns in incident list table footer more consistent with rest
  of footer ([#1393](https://github.com/Uninett/Argus/issues/1393))
- Dropped the "id"-column from the default incident columns config since most
  other colmns now are links to the details-page.

#### Fixed

- Make incident duration on details page more human readable
  ([#1196](https://github.com/Uninett/Argus/issues/1196))
- Center header text on incident details page
  ([#1298](https://github.com/Uninett/Argus/issues/1298))


## [1.35.0] - 2025-04-09

Remember to migrate the database, unwanted crud might have snuck into the
stored filters.

### Removed

- Dropped support for testing and running on Python 3.9 and Django 5.0.

### Fixed

- Fix broken Docker images to still work with SPA front-end
  ([#1310](https://github.com/Uninett/Argus/issues/1310))

### Frontend

The new frontend is now just about on par feature-wise with the old frontend,
though we do not aim for bug compatibility =)

#### Added

- Admins now see an admin link in the user menu dropdown
  ([#1261](https://github.com/Uninett/Argus/issues/1261))
- A new parameter `use_empty_filter` to the `incident_list_filter` function.
  `use_empty_filter` defaults to `False`.
  ([#1360](https://github.com/Uninett/Argus/issues/1360))
- Allow testing on Django 5.2 in anticipation of dropping Django 4.2.

#### Changed

- Change tristate selection from checkboxes to slider. More changes to come.
  ([#1048](https://github.com/Uninett/Argus/issues/1048))
- Made the incidents page more compact.
  ([#1246](https://github.com/Uninett/Argus/issues/1246))
- Grouped user preferences in user menu dropdown
  ([#1256](https://github.com/Uninett/Argus/issues/1256))
- Fixed styling of input fields in modals. Made all basic inputs (text, date,
  email etc) on the incidents, timeslots and destinations pages have the same
  universal design. ([#1311](https://github.com/Uninett/Argus/issues/1311))
- Improved the UX for forms on the profiles page.
  ([#1312](https://github.com/Uninett/Argus/issues/1312))
- Made styling of the tag badges on the details page more subtle.
  ([#1314](https://github.com/Uninett/Argus/issues/1314))
- Polished styling and alignment of the inputs in filterbox.
  ([#1316](https://github.com/Uninett/Argus/issues/1316))
- Incident tags that contain URL are now clickable on the incident detail page.
  ([#1329](https://github.com/Uninett/Argus/issues/1329))
- Switched to setting italic font using HTML instead of CSS for better
  accessibility. ([#1343](https://github.com/Uninett/Argus/issues/1343))
- Give the sections in the details page a drop shadow. This stranded the
  close/reopen button at the bottom, so it was moved to just above the list of
  events.
- In the details page: Make free text look better by breaking long lines and
  preserving newlines. Also make event types and ack/event author and timestamp
  stand out better.
- Made sure all non-button form inputs have `autocomplete="off"` set which
  fixes some annoying behavior in Firefox when filling in forms. This is
  documented in the troubleshooting guide.
- Make an abstraction for modals deleting things, as part of the modal cleanup.
- Modularized the incident pagination and improved it as per user feedback.
- Replaced the fancy days selector in the timeslots page with checkboxes.
- Support testing/running on Python 3.13. We need to stay on psycopg2 a while
  longer since we use PostgreSQL "infinity" for incident `end_time`.
- Upgraded all dependencies that could be upgraded and removes pytz as it is
  now unused.
- When showing the details url in the details page, use the generated absolute
  url from the `Incident.details_url` and the `Source.base_url`. Validates that
  the combination is valid and falls back to using the raw details url if not.

#### Fixed

- Bug with very long text in badges on the details page overflowing and
  becoming unreadable. ([#1244](https://github.com/Uninett/Argus/issues/1244))
- Made the height of the feeds on details page always conform to the max height
  of the details section. Any vertical overflow in the feed will now be
  scrollable. ([#1327](https://github.com/Uninett/Argus/issues/1327))
- Programmatically connected labels to corresponding inputs.
  ([#1332](https://github.com/Uninett/Argus/issues/1332))
- Removes "unacked" and "closed" from filterblobs.
  ([#1342](https://github.com/Uninett/Argus/issues/1342))
- Made filter selector more robust in general and fixed bugs:
  [#1344](https://github.com/Uninett/Argus/issues/1344),
  [#1353](https://github.com/Uninett/Argus/issues/1353),
  [#1355](https://github.com/Uninett/Argus/issues/1355).
  ([#1360](https://github.com/Uninett/Argus/issues/1360))
- Fixed color contrast for incident tags badges and table separators (temporary
  fix)
  ([#1375](https://github.com/Uninett/Argus/issues/1375),
  [#1378](https://github.com/Uninett/Argus/issues/1378))
- No longer erases a ticket url if attempting to save an invalid one when
  editing. There's an error message in a popup. Made ticket url always
  optional.
  ([#1371](https://github.com/Uninett/Argus/issues/1371))


## [1.34.1] - 2025-03-26

### Changed

- Updated README to highlight the deprecation of API v1, that the old
  frontend will soon not be supported and that Django will soon not support
  PostGRESQL older than 14.
- Updated the release checklist.

### Fixed

- Changed docker entrypoint script files that used the wrong path for `asgi.py`.

## [1.34.0] - 2025-03-26

**This release marks the beginning of the process towards argus-server 2.0!**

API V2 is hereby declared stable, and V1 is hereby deprecated.

Version 2 will *drop support* for API V1 *and* the old frontend. Please try the
new frontend and send us some feedback!

The next Django LTS, 5.2, will not support any PostgreSQL older than version
14, so please upgrade ASAP.

The incident list in the new frontend is now feature complete. The timeslots
page has been prettified but also has some bugs. There's lots of remaining UX
things to do.

### Added

- There's now a troubleshooting guide in the docs, for storing debugging tips.
- Made it possible to filter and search on `ticket_url` and `details_url` in
  admin.

### HTMX app

#### Added

- We now have a unique color per severity level.
  ([#996](https://github.com/Uninett/Argus/issues/996))
- Added button on the incident details page for autocreating a ticket.
  ([#1202](https://github.com/Uninett/Argus/issues/1202))
- Saved filters can now be both updated and deleted.
  ([#1207](https://github.com/Uninett/Argus/issues/1207), [#1231](https://github.com/Uninett/Argus/issues/1231))
- Added documentation on how to customize incident actions.
  ([#1212](https://github.com/Uninett/Argus/issues/1212))
- Added borders between table rows.
  ([#1253](https://github.com/Uninett/Argus/issues/1253))
- Added column to show combined status (openness+ackedness) as a color, for
  feature parity with the old frontend incident list.
- Made it possible to delete one or more timerecurrences from a timeslot.

#### Changed

NOTE! Version v1 of the API is hereby deprecated! It *will* be removed one
day. Update your glue services, please. Version v2 is the new stable API.

- Selecting '---' from existing filters now resets the filter parameters.
  ([#1144](https://github.com/Uninett/Argus/issues/1144))
- Simplified the filter select and filter create logic by refreshing the
  whole view on those operations.
  ([#1251](https://github.com/Uninett/Argus/issues/1251))
- The color of the status badges was changed to better represent either error
  or success state. The colors are universal across the themes.
  ([#1294](https://github.com/Uninett/Argus/issues/1294))
- Show empty list instead of error if tags do not match any incidents.
  ([#1302](https://github.com/Uninett/Argus/issues/1302))
- Otherwise uncaught exceptions are caught and logged. A less chatty version is
  shown to end users via messages.error.
- Improved the looks and UX of the timeslots page greatly. There are still
  remaining issues.
- In the status-badges use the same color for 'open' and 'unacked' and the same
  for 'closed' and 'acked'.
- It is now possible to add a link to the details page from any cell in the
  incident list, by using a different wrapper template. See the improved docs
  for customizing incident list columns.
- Moved notification links into the user menu, and removed the now sole
  remaining link that redundantly points to the incident list.
- Set default opacity of loading overlay to 50%.
- Several of our easily accessible users didn't like the frequent use of the
  reddish color as an accent in the "argus" theme, they prefer reserving
  reddish hues for extra important things. We've cut down on the use of
  "accent"-color everywhere: in the incidents page we now use the primary color
  instead, everywhere else we will fall back to the default for the
  tailwind/daisy class.

#### Fixed

- Users are now prohibited user from creating profile with same name as
  existing one.
  ([#1139](https://github.com/Uninett/Argus/issues/1139))
- Fixed a bug where the update filter modal was shown when trying to delete
  a given filter.
  ([#1266](https://github.com/Uninett/Argus/issues/1266))


## [1.33.0] - 2025-03-05

### Fixed

- Moved channels app from base settings to spa settings, where it belongs. The
  dependency had already been moved, so this avoids an ImportError on new
  installs. The spa frontend also needs CORS, but due to the complexity of when
  the middleware needs to be called, the cors app and middleware have not been
  moved, only the spa-specific setting.

### HTMx app

#### Added

- Add text field to filter incident list by tags
  ([#1044](https://github.com/Uninett/Argus/issues/1044))

#### Changed

- Improved formatting of incident datetimes on the details page by using
  `<time>`-tags, showing duration and end time only for stateful incidents, and
  showing duration for closed and still open incidents differently.


## [1.32.0] - 2025-03-03

### Added

- There's a new how to for customzing templates.
- Added MAINTAINING.rst so that maintenance tasks do not reside in only
  a single head.

### Changed

- The commit messages howto has been updated.
- Move the websockets stuff into the argus.spa directory and turn `argus.spa`
  into an app instead of `argus.ws`. This will make it easier to remove spa
  support.

### HTMx app

#### Added

- Implemented functionality that allows users to create new incident filters,
  and to select from existing ones via HTMX UI.
  ([#1045](https://github.com/Uninett/Argus/issues/1045))
- Add incident update interval as a preference
  ([#1174](https://github.com/Uninett/Argus/issues/1174))
- Add `HTMX_PATH` and `HYPERSCRIPT_PATH` setting
  ([#1183](https://github.com/Uninett/Argus/issues/1183))

#### Changed

- Update only the related media list when updating a destination.
  ([#1136](https://github.com/Uninett/Argus/issues/1136))
- Visiting the root page will now lead to be redirected to the
  /incidents/-page, triggering a login if necessary.
- Django's own templates for form widgets are now overridable
- Profiles page was updated and hopefullt improved thereby.
- There are lots of visual improvements
- More templates can be more easily customized

#### Fixed

- Show relevant error message on destination delete by passing the original
  exception message to the UI.
  ([#1147](https://github.com/Uninett/Argus/issues/1147))
- Do not run database query when importing IncidentFormFilter
  ([#1176](https://github.com/Uninett/Argus/issues/1176))


## [1.31.0] - 2025-01-17

Mostly changes to the new frontend this time around.

Two development-relevant changes:

- Refactor of incident-specific frontend pages, many files have new names
- How to define a preference has changed

There are visible changes to the destinations-page and profiles page as well.

### Added

- Added howto for how to easily toggle the use of django-debug-toolbar with the
  help of the extra/overriding-apps machinery and an environment variable.

### HTMx app

#### Added

- Centre destination page content.
  ([#1079](https://github.com/Uninett/Argus/issues/1079))
- Add vertical gap between collapse element and create form on HTMX
  destinations page. ([#1080](https://github.com/Uninett/Argus/issues/1080))

#### Changed

- Streamline definition and usage of preferences
  ([#1072](https://github.com/Uninett/Argus/issues/1072))
- Only update the related media list when deleting a destination.
  ([#1128](https://github.com/Uninett/Argus/issues/1128))
- Customizers beware: Major refactor in src/argus/htmx/incident(s) and
  src/argus/htmx/templates/htmx/incident(s).

  * All directories named "incidents" was changed to "incident".
  * The templates that defines columns in the incident list was moved to
    `htmx/incident/cells/`.
  * The template for selecting sources in the filterbox was moved to
    `htmx/incident/widgets/`.
  * Whenever there were plural view-names or url-names for incident-related
    views they were made singular.

  There will be empty directories left behind, `git` cannot do anything with
  these. Run `make clean` to delete cached files then find empty directories
  with `find . -type d -empty`. Delete them manually.
- Polished the looks of the profiles page. More to come!

#### Fixed

- Fix create destination form generating extra div when submitting.
  ([#1129](https://github.com/Uninett/Argus/issues/1129))


## [1.30.0] - 2024-12-19

Mostly changes to the alpha frontend

### Added

- Added docs for how to vendor a repo (copy one repo into another, preserving
  history).

### HTMX app

- Add HTMX version of the destinations page
  ([#1001](https://github.com/Uninett/Argus/issues/1001))
- Show user an error message in case a htmx partial request fails
  ([#1023](https://github.com/Uninett/Argus/issues/1023))
- Allow extending preferences page
  ([#1070](https://github.com/Uninett/Argus/issues/1070))
- Keep django messages in queue on htmx redirects or refreshes
  ([#1071](https://github.com/Uninett/Argus/issues/1071))

#### Added

- Replaced the placeholder notification profile page with a very ugly but
  functional one.
- Replaced the placeholder time-slots page with a very ugly but functional one.
- Added loading indicator to bulk action buttons

#### Changed

- Performance: Reduced the number of queries to preferences db table
  ([#1082](https://github.com/Uninett/Argus/issues/1082))
- Declared argus-theme as one with the light color scheme in order to always
  have reasonable fallbacks.
  ([#1088](https://github.com/Uninett/Argus/issues/1088))
- Generalized the multiselect dropdown widget used for the source field in the
  filterbox so that we can use it for other dropdowns on other pages.
- Renamed some directories and templates to give them better, more
  consistent names.

#### Fixed

- Fixed background color in input fields for argus-theme globally.
  ([#1088](https://github.com/Uninett/Argus/issues/1088))


## [1.29.0] - 2024-12-06

Mostly changes to the alpha frontend

### Added

- Add support for multple API tokens per user via django-rest-knox. For that
  reason, the old API endpoints for dealing with token authentication has been
  deprecated, and new endpoints have been added to v2 of the API.

### Changed

- We've copied the linting rules from argus-htmx, so anything that have not
  been merged yet might have to be updated to keep the linters happy.

### Deprecated

- All v1 API endpoints for dealing with phone numbers have been deprecated.
  Please see the v2 endpoints dealing with destinations instead.

### HTMx app

#### Added

- `ARGUS_HTMX_FILTER_FUNCTION` can take a callable or a dotted
  function path ([#1029](https://github.com/Uninett/Argus/issues/1029))
- Support incident filtering from incident list table columns

#### Changed

- Return user to login page on unauthenticated HTMx request
- Automatically close certain notification toasts

#### Fixed

- Keep column filters when autoreloading incident list
  ([#1033](https://github.com/Uninett/Argus/issues/1033))
- Fix incorrect width specifier in column filter input
  ([#1065](https://github.com/Uninett/Argus/issues/1065))


## [1.28.0] - 2024-11-29

This version marks the inclusion of our new, alpha web frontend. It does not do
everything the existing standalone frontend does yet, hence alpha. See docs for
how to test.

### Added

- We are now linting html with djLint
- Add new (unfinished) app: argus.htmx. Thiis is a new frontend written quite
  old-style, with HTML enhanced with HTMx. This used to live in its own app
  (PyPI: argus-htmx-frontend) and repo
  (https://github.com/Uninett/argus-htmx-frontend/) and is in the process of
  being completely merged with argus-server. All new issues and PR's should be
  made towards the argus-server repo. Unfinished branches and issues should be
  moved over here. PR's merged after the move will be moved by us.
- Added a short howto on how to try to fix a broken migration. Remember, it is
  always less stress to restore a backup!

### Changed

- We're switching from black to ruff, and will both lint and format code going
  forward.
- Use tox version 4 to run test suite


## [1.27.0] - 2024-11-13

### Added

- Added a database model to store user preferences. Remember to migrate!
- Added a new testenv to tox to easily regenerate the ER model. It needs
  regenerating thanks to the new model.


## [1.26.1] - 2024-11-08

### Changed

- Allow deletion in admin of "dormant" users, that is: users that have never
  created an event or incident. These frequently occur when testing new login
  methods.

### Fixed

- Logout via the React SPA frontend works again, the url has been corrected.


## [1.26.0] - 2024-10-29

This release is mainly to wrangle dependencies to the in-progress new frontend.

### Changed

- There's more detail on how to set up federated logins in the docs.
- Make `AUTHENTICATION_BACKENDS` setting mutable by making it a list, not
  a tuple.

### Fixed

- Do not run processes as `root` in Docker production container
  ([#921](https://github.com/Uninett/Argus/issues/921))


## [1.25.0] - 2024-10-24

### Added

- Make it easier to use the new HTMx-based frontend, with docs. The new
  frontend cannot be run simultaneously with the REACT SPA frontend as some
  settings conflict.


## [1.24.0] - 2024-10-22


### Added

- There's a new courtesy method on the User-model: `is_member_of_group()`.

### Changed

- Switched to running docker image on python 3.10 and postgres v14.
  ([#908](https://github.com/Uninett/Argus/issues/908))
- Make it possible to change any setting via the
  (EXTRA|OVERRIDING)\_APPS-machinery.
- Split out all the hard coded support for the REACT SPA frontend into
  a library.

  In the process, the following renames were done:

  - `ARGUS_COOKIE_DOMAIN` -> `ARGUS_SPA_COOKIE_DOMAIN` (environment variable)
  - `COOKIE_DOMAIN` -> `SPA_COOKIE_DOMAIN` (setting)
  - `ARGUS_TOKEN_COOKIE_NAME` -> `ARGUS_SPA_TOKEN_COOKIE_NAME` (hidden setting)

  How to deploy with support for this frontend has also changed, see the new
  documentation section "REACT Frontend". In short, it is necessary to change
  which settings-file to base the deployment on.


## [1.23.0] - 2024-10-10

This is the first version of Argus to be able to run on Django 5.1.

Support for Python 3.8 has been dropped.

The most visible changes are in the documentation.

### Removed

- As part of refactoring some authentication utility functions the function
  `get_psa_authentication_names()` has been removed as it wasn't used anywhere
  in Argus proper.

### Added

- Added a new section "Customization" to the docs, for customizations that go
  beyond integrations.
- Documented how to use (EXTRA|OVERRIDING)\_APPS to add app-specific
  middleware.
- There's a new howto, for how to regenerate the ER diagram in the docs.

### Changed

- So. Many. Refactors.
- There should be fewer warnings/log messages when visiting the autogenerated
  OpenAPI. There is one commit per change to help with future wrangling. There
  are still some warnings left; getting rid of those is left as an exercise to
  the reader.
- The favicon and template for the simple page generated on "/" are now
  replacable by adding an app at the start of INSTALLED\_APPS that has the new
  files.
- Plenty of dependencies and sub-dependencies were upgraded
- Django ValidationErrors are converted to DRF ValidationErrors. This makes it
  possible to move some validation from API model serializers to the actual
  model, which means validating only once and the API and future Django
  frontend seeing the same errors.
- Moved reference docs into their own section (as per Diátaxis), improved the
  looks and contents of the explanation and terms, and added a very brief
  explanation of each model.
- Moved site TEMPLATES and STATIC to a mini-app to make them replaceable via an
  app added before it in INSTALLED\_APPS.
- Removed `FilterSerializer` and `validate_jsonfilter` from the filter plugin
  mechanism since they just wrap `FilterBlobSerializer`. (This also means
  `FilterBlobSerializer` can no longer be in the same file as
  `FilterSerializer`.)

### Fixed

- Fix OpenAPI parameters for `incidents/` and `incidents/mine/`


## [1.22.1] - 2024-09-05


### Added

- Add method to get associated names of Incident levels
  ([#875](https://github.com/Uninett/Argus/issues/875))


## [1.22.0] - 2024-08-30


### Changed

- Refactored ticket creation code so the actual changing of the incident
  happens only in one place. Also moved the actual autocreation magic to
  utility functions (sans error-handling since that is response-type
  dependent). Made bulk changes of tickets actually create the ChangeEvents so
  that it behaves like other bulk actions and make it possible to get notified
  of changed ticket urls.
- Replace the setting `STATICFILES_STORAGE` with `STORAGES` to prepare for
  running on newer Djangos. See NOTES for details.

### Fixed

- Hopefully there will be fewer spurious test-failures thanks to explicitly
  creating the user connected to a sourcesystem. UniqueError, you won't be
  missd.
- Fixed broken link to dataporten authentication docs in README
  ([#broken-dataporten-link](https://github.com/Uninett/Argus/issues/broken-dataporten-link))
- Renamed 'docker-compose' to 'Docker Compose' in README
  ([#update-readme-command-naming](https://github.com/Uninett/Argus/issues/update-readme-command-naming))


## [1.21.0] - 2024-08-20


### Changed

- Make description editable
  ([#811](https://github.com/Uninett/Argus/issues/811))


## [1.20.1] - 2024-07-26

### Fixed

- `INCIDENT_LEVEL_CHOICES` was behaving oddly when debugging so it has been
  made a proper immutable constant.

## [1.20.0] - 2024-07-25


### Added

- Added method to check whether incident is acknowledged by a specific user
  group. ([#838](https://github.com/Uninett/Argus/issues/838))
- Made it possible to replace how Argus does filtering (for sending
  notifications and showing a list of incidents). See the howto "How to
  customize filtering".
- `OVERRIDING_APPS` and `EXTRA_APPS` now supports changing the
  MIDDLEWARE-setting. The key is "middleware" and the value is a dictionary of
  the dotted path of the middleware as the key, and an action as the value.
  Currently only the actions "start" and "end" is supported, putting the
  middleware at either the start of the list or the end, depending.

### Changed

BIG filter refactor/cleanup. All filter-stuff except the Filter-model has been
moved to a new app, argus.filter

- Move `Filter.filtered_incidents` to `argus.filter.queryset_filters.QuerySetFilter`
  - Change the signature so that it works on a filterblob, not a Filter model
    instance
- Ensure that the fallback filter, which is only relevant when sending
  notifications, is ignored everywhere else. First step in getting rid of this
  misfeature of a setting.
- Get rid of `NotificationProfile.filtered_incidents`, instead use
  `argus.filter.queryset_filters.QuerySetFilter.incidents_by_notificationprofile`
- Move Filter-dependent methods out of incident/models.py
- Move filter settings check to argus.filter
- Keep OpenAPI queryparam descriptions with their filters in argus.filter.filters
- Update and improve tests
- Move Filter `*_fits` methods to argus.filter.filterwrapper.FilterWrapper
- Move NotificationProfile `*_fits` methods to ComplexFilterWrapper
- Add docstring to argus.filter.filter
- Simplify/DRY existing filterwrapper methods, including tristate

### Fixed

- Removed one cause for spurious failures of tests
- Show infinite `end_time` as 'Still open' instead of datetime representation
  in email ([#793](https://github.com/Uninett/Argus/issues/793))
- Temporarily hide DestinationConfig from User admin in order to allow updating
  Users again. Undo if Django starts allowing JSONFields in UniqueConstraints.
  ([#822](https://github.com/Uninett/Argus/issues/822))
- Improve `/incident` endpoint response time by roughly 36% by pre-fetching
  incident tag data ([#837](https://github.com/Uninett/Argus/issues/837))


## [1.19.2] - 2024-05-28

### Added

- There is now a commented line in `argus.site.urls.urlpatterns` that if
  uncommented will allow logging into the API with username/password. This
  allows the use of the DRF HTML api to change records. This partially works
  with django-debug-toolbar and should ease some debugging sessions.

### Changed

- Optimized PUT/PATCH of incidents in API v2. Mainly by no longer replacing
  `Incident.search_text` on every Incident save, thereby avoiding looking up
  all events for that incident. The old behavior was fine when there was only
  a handful of events per incident but we can no longer assume that.

## [1.19.1] - 2024-05-16

### Fixed

- Fixed bug preventing naive printing of TimeRecurrences, triggering
  a traceback

## [1.19.0] - 2024-05-15

*Backwards-incompatible change*: Because it is now possible to filter on
multiple event types instead of just one, both API V1 and API V2 has changed
its schema for Filter.filter. See NOTES.md for details.

### Removed

- Removed `"event_type"` from the V1 Filter API, it should only have been
  available in V2 (since it was new) and it has never been in use by the
  frontend. ([#699](https://github.com/Uninett/Argus/issues/699))

### Added

- Add filtering of events by a list of event types
  ([#699](https://github.com/Uninett/Argus/issues/699))
- Add howto about how to set up and test federated login, using GitHub as an
  example. ([#803](https://github.com/Uninett/Argus/issues/803))
- Extend the usefulness of `OVERRIDE_APPS` and `EXTRA_APPS` by adding support
  for Django template engine context processors. Any context processors are
  added to the end of the list.
  ([#810](https://github.com/Uninett/Argus/issues/810))

### Changed

- Change how the description of a change event is formatted so that it is
  always consistent (not to mention DRY).
  ([#809](https://github.com/Uninett/Argus/issues/809))


## [1.18.0] - 2024-05-07


### Added

- New in the API: Allow sources to delete their own incidents, as well as allow
  superusers to delete any incident.
  ([#804](https://github.com/Uninett/Argus/issues/804))

### Changed

- Allow replacing Incident.metadata with another json blob via API, no
  questions asked, nothing to see here.
  ([#807](https://github.com/Uninett/Argus/issues/807))


## [1.17.0] - 2024-05-03


### Added

- Add a possibility to filter incidents by start time in incident admin list
  ([#739](https://github.com/Uninett/Argus/issues/739))
- Added an optional JSONField "metadata" to incident. This can be used for any
  additional info the glue-service would like to store on the incident that
  needs more structure than tags. The field has been added to the V2
  IncidentSerializer but we do not plan to expose it in the frontend.
- Added documentation on how to safely test notifications.
- Added simple support for pluggable django-apps. The setting `OVERRIDING_APPS`
  is loaded first in `INSTALLED_APPS` and `urls.py`, and can override templates
  and views. The setting `EXTRA_APPS` is safer, it is loaded last in
  `INSTALLED_APPS` and `urls.py` and can therefore only add additional
  templates and views.

### Changed

- When editing a notification profile in the admin UI, only the profile owner's
  own filters are now listed as available for selection.
  ([#735](https://github.com/Uninett/Argus/issues/735))
- Linked up the second column in the admin incident list to the details view in
  addition to the default first column because the first column is currently an
  optional field. If the field has no value there can also not be a link.
- Update the release checklist in `docs/` to current practices and turn it into
  a howto.

### Fixed

- Show fully qualified details URL in emails
  ([#744](https://github.com/Uninett/Argus/issues/744))
- Fix internal server error in timeslot admin due to removed method
  ([#797](https://github.com/Uninett/Argus/issues/797))


## [1.16.0] - 2024-04-23

### Added

- Added development dependency on django-debug-toolbar to make it easy to use.
- Adds more capability to the stresstest command, including incident creation
  verification, bulk ACKing and timeout configuration.
  ([#641](https://github.com/Uninett/Argus/issues/641))
- Add possibility to set fields when creating fake incidents in Django admin
  ([#669](https://github.com/Uninett/Argus/issues/669))
- Show user and filter by user in notification profile admin
  ([#734](https://github.com/Uninett/Argus/issues/734))
- Add cli command to toggle notification profile activation
  ([#747](https://github.com/Uninett/Argus/issues/747))
- Add admin action to change activation of profiles
  ([#748](https://github.com/Uninett/Argus/issues/748))
- Add API documentation for GET responses
  ([#752](https://github.com/Uninett/Argus/issues/752))
- Added an informational page on /, with favicon, in order to cut down on some
  common 404 log messages and set up the static files system properly.

### Changed

- Switched official Docker image to serve using gunicorn+uvicorn
  ([#766](https://github.com/Uninett/Argus/issues/766))
- Changed how tristates (open, acked, stateful) are logged in order to improve
  debuggability.
- Return False and log if sms-to-email has trouble with the email server.
- To improve debugability: Change how sending notifications are logged so that
  there's a log both when sending succeds and when it fails.

### Fixed

- Changed references to docs for Django 4.2
  ([#746](https://github.com/Uninett/Argus/issues/746))
- Do not allow used destinations to be deleted
  ([#753](https://github.com/Uninett/Argus/issues/753))
- Fix typo in admin that prevented sorting on incident id


## [1.15.0] - 2024-04-10

Due to the removal of the django-multiselectfield dependency it is vitally
important to upgrade to *this* version *after* correctly having upgraded to
1.14.3 (the previous version).

Be sure to migrate the database:

```console
$ python manage.py migrate
```

This version supports Django 4.2 and newer.

### Changed

- Drop all support for Django 3.2. No version-specific requirements for 3.2 are
  included anymore, and we no longer test on 3.2.

### Removed

- Remove django-multiselectfield dependency ([#707](https://github.com/Uninett/Argus/issues/707))

## [1.14.3] - 2024-04-09

This release changes the database in order to get rid of a dead dependency,
make sure to run migrations.

This version can run on Django 5.0 if necessary. Install the dependencies in
`requirements-django50.txt` if so.

This is the last version that supports Django 3.2.

### Added

- Add filtering of incident list by notificationprofile

  This returns all incidents that are included in filters that are connected to
  that notificationprofile
- Added support for running and testing on Django 5.0

### Changed

- Change TimeRecurrence.days from MultiSelectField to ArrayField
  ([#707](https://github.com/Uninett/Argus/issues/707))
- Updated lots of depenendcies in order to run on Django 5.0

## [1.14.2] - 2024-02-15

This version can run on Django 4.2. In production, ensure that the list of
entries in `CSRF_TRUSTED_ORIGINS` are absolute urls, all starting with
`https://`.

### Added

- Add filtering of incident list by filter

  This returns all incidents that are included in the filter
  ([#244](https://github.com/Uninett/Argus/issues/244))
- Allow running and testing on Python 3.12
- Added towncrier to automatically produce changelog
- Add two development dependencies

  While `tox` doesn't need to be in the venv, it DOES currently need to be less
  than version 4.

  `build` is useful for debugging pip errors and pip-compile trouble.
  Whenever pip-compile (via `tox -e upgrade-deps` for instance) fails with

  ```
  Backend subprocess exited when trying to invoke get_requires_for_build_wheel
  Failed to parse /PATH/pyproject.toml
  ```

  run `python -m build -w` to see what `build` is actually complaining about.

  See also https://github.com/pypa/build/issues/553
- Add the "admin_url" field to the user serializer. This is so that the
  frontend can show a link to the Django admin.
- Added the possibility to filter incident by a given list of ids

### Fixed

- Fixed posting/updating notification profiles without name

### Changed

- Updated a lot of (sub)dependencies to allow running on newer pythons and
  newer Djangos, and to quiet dependency bots

## [1.14.1 - 2023-12-05]

### Changed

- Restructured documentation about integrations

## [1.14.0] - 2023-01-03

Incomplete changelog.

Due to a change in the signature of `NotificationPlugin.send()`, 3rd party
plugins will need to mark better which versions of argus-server they work with
in their dependencies-list. The old-style plugins work on 1.9-1.13.

### Added
- Add the "installed" field to the media serializer. This is so that the
  frontend can detect media used that is no longer installed on the backend.

### Fixed
- Ensure the right notifications go to the right destinations when sending many
  of each.

### Changed
- Change the signature of the notification-plugin `send`-method to avoid
  passing in the database
- Log profile owners name when checking profiles
- Constrain subdependencies in a better way
- Send one email per email-address so as to not leak who else gets that email.
- Remove the `Filter.filter_string`-field from the database. We're not using it
  anymore and shouldn't ever use it by accident either.

## [1.13.0] - 2023-09-19

Works with argus-frontend 1.11 and newer.

### Added
- Lint for critical problems before testing in Github CI, to speed things up
- Added config-file for building docs at readthedocs
- Add inline destinations to user edit page in admin
- Add management command for listing filters
- Add management command for bulk acting on incidents matching a given filter

### Fixed
- Raise validation error on posting incident with tags without tag key

### Changed
- Update Django patch versions and various dependencies
- Drop support for Python 3.7. Github's CI/CD was sufficiently different from
  testing on local (different setuptools-version used maybe?) that we had
  a "fun" goose chase finding and upgrading the sub-dependency that broke the
  build.
- Remove all remaining uses of `Filter.filter_string`, replace with
  Filter.filter, in preparation of removing the actual `filter_string` field
  from the database.

  The API v1 still accepts `filter_string` but it is optional. It will prefer
  the data in `filter`. v2 ignores the presence or absence of `filter_string`
  entirely.

## [1.12.4] - 2023-09-04

### Changed
- Ensure that the start event is created *after* the incident has its tags so
  that notification filters with tags trigger correctly. The signal that
  creates the first event is gone, but the signal that triggers on creation of
  the first event is not, that will have to wait until we utilize a queue.

## [1.12.3] - 2023-08-31

### Changed
- Change what is logged on notification sending in order to ease solving
  problems in production

## [1.12.2] - 2023-06-27

### Fixed
- When sending a notification in production a typo lead to an exception that
  prevented sending the notification but was otherwise hidden from the end
  user.

## [1.12.1] - 2023-05-04

### Fixed
- Typo in code (that could have been found by flake8) lead to acks not working
  when notifications are turned on

## [1.12.0] - 2023-05-03

### Added
- More tests. Lots.
- Add docs for how to write a notification plugin
- Add a new command "stresstest", for stress-testing the API
- Start a process for revealing to the frontend which media plugins are
  actually installed
- Log a warning if a medium in the Media-table does not have a plugin installed
- Mention cookiecutter-template for tickets in the ticket docs
- Support running on Django 4.2
- Documented how to use email to send notifications to Slack
- Make the auth-method endpoint also show that username/password is supported
- In ticket-automation, show which fields were configured but not found in the
  generated ticket

### Fixed
- Lots of formatting-bugaboos in the docs
- Allow updating of a timeslot with an empty time recurrence list, which
  results in all time recurrences to be removed from the timeslot

### Changed
- Optimize and refactor bulk api operations
- Change how media plugins are accessed in order to avoid/control some exceptions
- Start the process of getting rid of `Filter.filter_string` by ensuring the
  info in `filter_string` is also in `Filter.filter`
- Correct some api examples in docs
- Only fork a new process to send notifications if there are any notifications
  to send
- Upgrade lots of dependencies
- Support explicit timestamp in `Incident.set_open/set_closed`
- Change how parameter names to SerializerMethodFields are set up
- Improved ticket docs
- Fixed typos
- Simplify generation of frozen dependency list: trust pyproject.toml

## [1.11.1] - 2023-02-16

### Added
- Coverage of the notificationprofile app was improved with several new tests

### Fixed
- CORS-headers do not want explicit port numbers if the ports are the default
  for their type, that is: 80 for http or 443 for https. This lead to CORS not
  working if there was an explicit port in the `ARGUS_FRONTEND_URL` setting,
  which used to generate a CORS entry for the frontend. Such port numbers are
  now stripped when generating the CORS header.

## [1.11.0] - 2023-02-02

With this version, the API for bulk changes of incidents and sending of
notifications to new and interesting destinations via destination plugins has
been frozen, and should be ready for use, completing what was started in 1.10.

## Added
- Add default HTML template for autocreated tickets
- Also include frontend-url to incident in incident-serializer
- Output XML test-reports and set up github actions for it
- Show installed plugins in the metadata view

### Fixed
- Fix API for adding events in bulk, with tests
- Fix API for bulk acking, with tests

### Changed
- Improved OpenAPI by adding some more docstrings
- Updated version of github-actions actions
- Use better exceptions for ticket plugins
- Change how/where change-events are created
- Move tests for included destinations to individual files

## [1.10.2] - 2022-12-13

### Changed
- Renamed the ticket creation endpoint via plugin from `/ticket/` to `/automatic-ticket/`
- Refactored the view tests for NotificationProfile
- Explicitly set language in sphinx conf, silencing a warning

## [1.10.1] - 2022-12-08


## [1.10.1] - 2022-12-08


## [1.10.0] - 2022-11-17

### Added
- Added support for testing on Python 3.11 and Django 4.0, 4.1
- Plugin system for ticket system integrations, documented in the new "Ticket
  system settings" sections.
- Add a production-oriented Dockerfile and use Github to build and store images
- New API endpoint to create a new ticket in an external ticket system
- Add docs about notification plugins
- Added the possibility to filter notifications by event-type
- Added a management command that will create incidents if a source token is
  close to expiring
- Added an endpoint to set `ticket_url` of incidents in bulk
- Added an endpoint to create events for incidents in bulk

### Fixed
- Changed when the Media-table is synced with settings `MEDIA_PLUGINS` to avoid
  dev/prod-settings leaking into the tests

### Changed
- Flatten the json structure for posting acknowledgements.
- Improve Sonar Cloud settings, like just testing for Python 3

## [1.9.0] - 2022-11-08

### Added
- Add test for updating phone number in V1
- Add test for posting tag with invalid key
- Added an endpoint to acknowledge incidents in bulk
- Added an endpoint to get a refreshed auth token.
- Add a filter to find incidents with a duration longer than a given amount of
 minutes.
- Added tests for previously untested incident endpoints
- A Makefile that cleans away generated files

### Fixed
- Validate that user doesn't have destination with same settings before
  creating/updating destination
- Properly catch tag validtion errors
- The FilterFactory no longer leads to random UniqueViolations on testing

## [1.8.1] - 2022-10-28

### Fixed
- Fix typo that prevented SMS messages from being sent.

## [1.8.0] - 2022-10-06

### Added
- A notification profile can now have a name.
- Docstrings and type hints to functions of media plugins.
- Added tests for the email and sms destination serializer in case of invalid
  input for updating.
- Added tests for the incident, event and tag serializer
- Added endpoint that returns True if another user has a destination with the
  same medium and settings as the destination with the given primary key
- Add tests for filtering on stateful/statelss and open/closed incients.
- Add SMSNotification plugin to MEDIA_PLUGINS in development settings.

### Fixed
- Fix a notification profile test to include the phone number changes.
- Broken links and formatting in documentation.
- Fix notification profile serializer test to actually change phone number when
  updating.
- Make code snippets visible in release checklist in documentation.
- Validate tags before adding them to an incident
- Disallow the use of `argus` as username when creating admin user via the `initial_setup` script.

### Changed
- One timeslot can now be used by multiple notification profiles.
- Replaced wildcard imports with specific imports.
- Moved the notification profile Github test to parent folder and added
  regression tag.
- Renamed notification profile serializer tests to be more descriptive and
  added integration test tags.
- Improve query in notification profile signal test and add clarifying comment.
- Ran black again on whole code base.
- In media plugins rename the function `is_deletable` to
  `raise_if_not_deletable` and make it raise an error if a destination is not
  deletable.
- Split up and rename notification profile model tests

### Dependencies
- Upgrade from pyjwt 2.0.1 to 2.4.0
- Upgrade from django 3.2.13 to 3.2.15
- Upgrade from black 20.8b1 to 22.3.0 in pre-commit

## [1.7.0]

### Changed

- Clean away database tables rendered unnecessary due to changes in 1.6.0
- Modernize packaging. Package-building is all in pyproject.toml, tools are

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
