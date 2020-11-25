# Argus
[![build badge](https://github.com/Uninett/Argus/workflows/build/badge.svg)](https://github.com/Uninett/Argus/actions)
[![codecov badge](https://codecov.io/gh/Uninett/Argus/branch/master/graph/badge.svg)](https://codecov.io/gh/Uninett/Argus)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Argus is a platform for aggregating incidents across network management systems, and
sending notifications to users. Users create notification profiles that define which
incidents they subscribe to.

This repository hosts the backend built with Django, while the frontend is hosted here:
https://github.com/Uninett/Argus-frontend.

## Installation

There are several ways to install Argus.

### Prerequisites

#### Requirements

* Python 3.7+
* pip

#### Optional requirements

* **Redis**
  is recommended if you are going to run the frontend.
  Redis backs the websockets, in order to push realtime updates to the frontend.
* [Argus-frontend](https://github.com/Uninett/Argus-frontend/)
* PostgreSQL
* Docker and docker-compose to run Argus in Docker

#### Optional: Dataporten registration

Dataporten is required to use the Argus-frontend.
Refer to the [Dataporten](doc/dataporten.rst) section of the documentation to learn
about Dataporten registration, and how to set it up with Argus.

### Install Argus using pip

Download the source code first.
```console
$ git clone https://github.com/Uninett/Argus.git
$ cd Argus
```

We recommend to use virtualenv or virtaulenvwrapper to create
a place to stash Argus' dependencies.

Create and activate a Python virtual environment.
```console
$ python -m venv venv
$ source venv/bin/activate
```

Install Argus' requirements into the virtual env.
```console
$ pip install -r requirements.txt
```

Run the initial Argus setup, then start the server.
```console
$ python manage.py initial_setup
$ python manage.py runserver
```

You will find Argus running at http://localhost:8000/.

### Setup Argus using Docker Compose

Again, download the source code first.
```console
$ git clone https://github.com/Uninett/Argus.git
$ cd Argus
```

Running Argus with docker-compose is as simple as
```console
$ docker-compose up
$ docker-compose exec argus-api django-admin initial_setup
```

You will find Argus running at http://localhost:8000/.

### Install Argus via PyPI

You can also install Argus with `pip` via PyPI. The package name is `argus-server`:
```console
$ pip install argus-server
```

If you are using the PyPI package in production, please note: The file
`requirements.txt` contains the versions of dependencies that the release was
tested on.
To update all the dependencies to recent versions, use `pip-compile`:

```console
$ pip install pip-tools
$ pip-compile -o your-updated-requirements.txt
$ pip install --upgrade -r your-updated-requirements.txt
```

## Site- and deployment-specific settings in Argus

Site-specific settings can either be set using environment variables, using a
`settings.py` file, or a combination of both.

For more information on both methods and a list of the settings, consult the
documentation section on
[site-specific settings](docs/site-specific-settings.rst).


## Running Argus in development

### Step 1: Installation

Check out either [the installation instructions for pip](#install-argus-using-pip) or
[use docker-compose](#setup-argus-using-docker-compose) to get Argus up and
running.

When using pip, perform this step to install the dependencies into your virtual env:
```console
$ pip install -r requirements/prod.txt
$ pip install -r requirements/dev.txt
```

Docker-compose will do this automatically.

### Step 2: Setting environment variables and Django settings

Copy the `cmd.sh-template` to `cmd.sh` and make it executable
```console
$ cp cmd.sh-template cmd.sh
$ chmod u+x cmd.sh
```
Now set the environment variables in the file using an editor.

Required settings in `cmd.sh` are

- `DATABASE_URL`,
- `DJANGO_SETTINGS_MODULE` and
- `SECRET_KEY`.

The `DATAPORTEN` variables are only required to test the frontend.
Refer to the dataporten section of
[setting site-specific settings](docs/site-specific-settings.rst) for details.

`DJANGO_SETTINGS_MODULE` can be set to `argus.site.settings.dev`.

If you need more complex settings than environment variables and ``cmd.sh`` can provide,
we recommend having a `localsettings.py` in the same directory as `manage.py` with any
overrides.

Refer to the [development notes](doc/development.rst) for further details and
useful hints on managing Argus in development mode.

### Code style

Argus uses black as a source code formatter. Black will automatically install
with the [dev requirements](requirements/dev.txt).

A pre-commit hook will format new code automatically before committing.
To enable this pre-commit hook, run

```console
$ pre-commit install
```


## Running tests

Given that Argus is installed and configured as described above,
this command is the most basic option to run the tests.
```console
$ python manage.py test
```

If you have installed `tox`, the following command will
test Argus code against several Django versions, several Python versions, and
automatically compute code coverage.
```console
$ tox
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
