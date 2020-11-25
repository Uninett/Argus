# Argus
[![build badge](https://github.com/Uninett/Argus/workflows/build/badge.svg)](https://github.com/Uninett/Argus/actions)
[![codecov badge](https://codecov.io/gh/Uninett/Argus/branch/master/graph/badge.svg)](https://codecov.io/gh/Uninett/Argus)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Argus is a platform for aggregating incidents across network management systems, and sending notifications to users. Users create notification profiles that define which incidents they subscribe to.

This repository hosts the backend built with Django, while the frontend is hosted here: https://github.com/Uninett/Argus-frontend.

## Installation

There are several ways to install Argus.

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
  * Replace `{server_url}` with the URL to the server running this project, like `http://localhost:8000`
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

## Site- and deployment-specific settings

Site-specific settings can either be set using environment variables, using a
`settings.py` file, or a combination of both.

For more information on both methods and a list of the variables, consult the
documentation section on
[Setting site-specific settings](docs/site-specific-settings.rst).

## Running tests locally

This command is the most basic option to run the tests.
```
python manage.py test
```

If you have installed `tox`, the following command will
test several django versions, several python versions, and
automatically compute code coverage.
```
tox
```
An [HTML coverage report](htmlcov/index.html) will be generated.
Refer to [tox.ini] for further options.

### Mock data
#### Generating
```sh
PYTHONPATH=src python src/argus/incident/fixtures/generate_fixtures.py
```
This creates the file `src/argus/incident/fixtures/incident/mock_data.json`.

#### Loading
```sh
python manage.py loaddata incident/mock_data
```

## Running Argus in development


### Step 1: Installation

Check out the code repository and refer to [Project setup](#project-setup) or
[Alternative setup using Docker Compose](#alternative-setup-using-docker-compose)
in the [Setup section](#setup).

1. Create and activate a virtualenv (as described in
  [Install Argus using pip](#install-argus-using-pip)).
2. Fill the activated virtualenv with dependencies:
```
pip install -r requirements/prod.txt
pip install -r requirements/dev.txt
```

### Step 2: Setting environment variables and Django settings

Copy the `cmd.sh-template` to `cmd.sh` and make it executable
```
$ cp cmd.sh-template cmd.sh
$ chmod u+x cmd.sh
```
Now set the environment variables in the file using an editor.

Tip: You may find it useful to have several `cmd.sh` files for different
purposes, for instance to invoke different databases.
They can be named `cmd-local.sh`, `cmd-prod.sh` and `cmd-demo.sh`, to name
a few.

Do not check these files into version control, since they contain passwords and
sensitive data.

Required settings on `cmd.sh` are
* `DATABASE_URL`,
* `DJANGO_SETTINGS_MODULE` and
* `SECRET_KEY`.

The `DATAPORTEN` variables are required to test the frontend.
Refer to https://dashboard.dataporten.no/ for more information or to create a
new application.

`DJANGO_SETTINGS_MODULE` can be set to "argus.site.settings.dev".
We recommend having a `localsettings.py` in the same directory as `manage.py`
with any overrides.

This file also does not belong in version control since it reflects
a specific developer's preferences.

Settings can be tested in `localsettings.py` and moved to the other settings
files later.

Tip: If you copy the entire logging-setup from "argus.site.settings.dev" to
`localsettings.py` remember to set `disable_existing_loggers` to `True`.
Otherwise, logentries will appear twice.

#### Coding style

Argus uses black as a source code formatter. Black will automatically install
with the [dev requirements](requirements/dev.txt).

A pre-commit hook will format new code automatically before committing.
To enable this pre-commit hook, run

```
pre-commit install
```
inside your virtual env.

#### Debugging tips

To test/debug notifications as a whole, use the email subsystem (Media: Email in a NotificationProfile).
Set EMAIL_HOST to "localhost", EMAIL_PORT to "1025", and run a dummy mailserver:

```
$ python3 -m smtpd -n -c DebuggingServer localhost:1025
```

Notifications sent will then be dumped to the console where the dummy server runs.
