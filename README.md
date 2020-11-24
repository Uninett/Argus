# Argus
[![build badge](https://github.com/Uninett/Argus/workflows/build/badge.svg)](https://github.com/Uninett/Argus/actions)
[![codecov badge](https://codecov.io/gh/Uninett/Argus/branch/master/graph/badge.svg)](https://codecov.io/gh/Uninett/Argus)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Argus is a platform for aggregating incidents across network management systems, and sending notifications to users. Users build notification profiles that define which incidents they subscribe to.

This repository hosts the backend built with Django, while the frontend is hosted here: https://github.com/Uninett/Argus-frontend.

## Installation

There are several ways to install Argus.

In development, check out the code repository check out the code repository
and refer to [Project setup](#project-setup) or
[Alternative setup using Docker Compose](#alternative-setup-using-docker-compose)
in the [Setup section](#setup).

## Setup

### Requirements
* Python 3.7+
* pip

### Optional
* Redis
  If you are going to run the frontend we also recommend you have Redis running
  to back the websockets, in order to push realtime updates to the frontend.
* [Argus-frontend](https://github.com/Uninett/Argus-frontend/)
* PostgreSQL
* Docker and docker-compose

### Dataporten setup
* Register a new application with the following redirect URL: `{server_url}/oidc/complete/dataporten_feide/`
  * `{server_url}` must be replaced with the URL to the server running this project, like `http://localhost:8000`
* Add the following permission scopes:
  * `profile`
  * `userid`
  * `userid-feide`

### Install Argus using pip

We recommend to use virtualenv or virtaulenvwrapper to create
a place to stash all dependencies.

Create and activate a Python virtual environment.
```
python -m venv venv
source venv/bin/activate
```
Install Argus' requirements into the virtual env.
```
$ pip install -r requirements.txt
```
Run the initial Argus setup, then start the server.
```
python manage.py initial_setup
python manage.py runserver
```
Visit http://localhost:8000/.

### Setup Argus using Docker Compose

```
docker-compose up
docker-compose exec argus-api django-admin initial_setup
```
Visit http://localhost:8000/

###  Install Argus via PyPI

You can also install Argus with `pip` via PyPI. The package name is `argus-server`:

```
$ pip install argus-server
```

If you are using the PyPI package in production, please note: The file
`requirements.txt` contains the versions of dependencies that the release was
tested on.
To update all the dependencies to recent versions, use `pip-compile`:

```
$ pip install pip-tools
$ pip-compile -o your-updated-requirements.txt
$ pip install --upgrade -r your-updated-requirements.txt
```

### Site- and deployment-specific settings

Site-specific settings are set as per 12 factor, with environment variables. For more details, see the relevant section in the docs: [Setting site-specific settings](docs/site-specific-settings.rst).

A recap of the environment variables that can be set by default follows.

#### Environment variables

* ARGUS_DATAPORTEN_KEY, which holds the id/key for using dataporten for
  authentication.
* ARGUS_DATAPORTEN_SECRET, which holds the password for using dataporten for
  authentication.
* ARGUS_COOKIE_DOMAIN, the domain the cookie is set for
* ARGUS_FRONTEND_URL, for redirecting back to frontend after logging in through
  Feide, and also CORS. Must either be a subdomain of or the same as
  ARGUS_COOKIE_DOMAIN
* ARGUS_SEND_NOTIFICATIONS, True in production and False by default, to allow supressing notifications
* DEBUG, 1 for True, 0 for False
* TEMPLATE_DEBUG. By default set to the same as DEBUG.
* DEFAULT_FROM_EMAIL, the email From-address used for notifications sent via email
* EMAIL_HOST, smarthost (domain name) to send email through
* EMAIL_HOST_USER, (optional) if the host in EMAIL_HOST needs authentication
* EMAIL_HOST_PASSWORD, (optional) password if the smarthost needs that
* EMAIL_PORT, in production by default set to 587
* SECRET_KEY, used internally by django, should be about 50 chars of ascii
  noise (but avoid backspaces!)

There are also settings (not env-variables) for which notification plugins to use:

DEFAULT_SMS_MEDIA, which by default is unset, since there is no standardized
way of sending SMSes. See **Notifications and notification plugins**.

DEFAULT_EMAIL_MEDIA, which is included and uses Django's email backend. It is
better to switch out the email backend than replcaing this plugin.

*A Gmail account with "Allow less secure apps" turned on, was used in the development of this project.*

### Production gotchas

The frontend and backend currently needs to be on either the same domain or be
subdomains of the same domain (ARGUS_COOKIE_DOMAIN).

When running on localhost for dev and test, ARGUS_COOKIE_DOMAIN may be empty.

### Running tests locally

Either:

* `python manage.py test`

Or, if you have installed `tox`:

* tox

The latter will test several django version, several python versions, and
automatically compute coverage. An [HTML coverage report](htmlcov/index.html)
is also autogenerated.

See `tox.ini` for what other things tox can do.

### Mock data
##### Generating
```sh
PYTHONPATH=src python src/argus/incident/fixtures/generate_fixtures.py
```
This creates the file `src/argus/incident/fixtures/incident/mock_data.json`.

##### Loading
```sh
python manage.py loaddata incident/mock_data
```

### Running in development

The fastest is to use virtualenv or virtaulenvwrapper or similar to create
a safe place to stash all the dependencies.

1. Create the virtualenv
2. Fill the activated virtualenv with dependencies:

```
$ pip install -r requirements/prod.txt
$ pip install -r requirements/dev.txt
```

Copy the `cmd.sh-template` to a new name ending with ".sh", make it executable
and set the environment variables within. This file must not be checked in to
version control, since it contains passwords. You *must* set DATABASE_URL,
DJANGO_SETTINGS_MODULE and SECRET_KEY. If you want to test the frontend you
must also set all the DATAPORTEN-settings. Get the values from
https://dashboard.dataporten.no/ or create a new application there.

For the database we recommend postgres as we use a postgres-specific feature in
the Incident-model.

DJANGO_SETTINGS_MODULE can be set to "argus.site.settings.dev" but we recommend
having a `localsettings.py` in the same directory as `manage.py` with any
overrides. This file also does not belong in version control since it reflects
a specific developer's preferences. Smart things first tested in
a localsettings can be moved to the other settings-files later on. If you copy
the entire logging-setup from "argus.site.settings.dev" to "localsettings.py"
remember to set "disable_existing_loggers" to True or logentries will occur
twice.

This repository uses black as a code formatter. Black will automatically install
with the [dev requirements](requirements/dev.txt).

A pre-commit hook formats new code automatically before committing.
To enable this pre-commit hook, please run

```
pre-commit install
```

### Debugging tips

To test/debug notifications as a whole, use the email subsystem (Media: Email in a NotificationProfile).
Set EMAIL_HOST to "localhost", EMAIL_PORT to "1025", and run a dummy mailserver:

```
$ python3 -m smtpd -n -c DebuggingServer localhost:1025
```

Notifications sent will then be dumped to the console where the dummy server runs.
