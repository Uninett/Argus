# Argus
[![build badge](https://github.com/Uninett/Argus/workflows/build/badge.svg)](https://github.com/Uninett/Argus/actions)
[![codecov badge](https://codecov.io/gh/Uninett/Argus/branch/master/graph/badge.svg)](https://codecov.io/gh/Uninett/Argus)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![docs badge](https://readthedocs.org/projects/argus-server/badge/?version=latest&style=flat)](http://argus-server.rtfd.io/en/latest/)

Argus is a platform for aggregating incidents across network management systems, and
sending notifications to users. Users create notification profiles that define which
incidents they subscribe to. See [Argus docs](http://argus-server.rtfd.io/en/latest/) for more details.

This repository hosts the backend built with Django. There is also a
[REACT SPA frontend](https://github.com/Uninett/Argus-frontend).


See also the the [Python client library](https://github.com/Uninett/pyargus).

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

Dataporten authentication is supported by Argus and can be used to log into
Argus-frontend.
Refer to the [Dataporten](http://argus-server.rtfd.io/en/latest/dataporten.html) section of the documentation to learn
about Dataporten registration, and how to set it up with Argus.

### Install Argus using pip

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

Now change and adapt [Argus' settings](#settings-in-argus) according to your needs.

Run the initial Argus setup, and make note of the admin password that is generated:

```console
$ python manage.py initial_setup
******************************************************************************

  Created Argus superuser "admin" with password "2S0qJbjVEew0GunL".

   Please change the password via the admin interface.

******************************************************************************
```

Then run the Argus API server:

```console
$ python manage.py runserver
```

### Setup Argus using Docker Compose

Download the source code first.
```console
$ git clone https://github.com/Uninett/Argus.git
$ cd Argus
```

Running Argus with docker-compose is as simple as
```console
$ docker-compose up
```

Run the initial Argus setup, and make note of the admin password that is generated:

```console
$ docker-compose exec api django-admin initial_setup
******************************************************************************

  Created Argus superuser "admin" with password "ns6bfoKquW12koIP".

   Please change the password via the admin interface.

******************************************************************************
```


You will find Argus running at http://localhost:8000/.

## Settings in Argus

Site-specific settings can either be set using environment variables, using a
`settings.py` file, or a combination of both.

For more information on both methods and a list of the settings, consult the
documentation section on
[site-specific settings](http://argus-server.rtfd.io/en/latest/site-specific-settings.html).


## Running Argus in development

### Step 1: Installation

You can use docker-compose to conveniently setup a complete dev environment for Argus,
including PostgreSQL. Instructions
[are provided above](#setup-argus-using-docker-compose).

To do a manual install instead, follow these steps.

Download the source code first.
```console
$ git clone https://github.com/Uninett/Argus.git
$ cd Argus
```

We recommend using virtualenv or virtaulenvwrapper to create
a place to stash Argus' dependencies.

Create and activate a Python virtual environment.
```console
$ python -m venv venv
$ source venv/bin/activate
```

Install Argus' requirements into the virtual env.
```console
$ pip install -r requirements-django32.txt
$ pip install -r requirements/dev.txt
```

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

The `DATAPORTEN` variables are optional. Refer to the dataporten section of
[setting site-specific settings](http://argus-server.rtfd.io/en/latest/site-specific-settings.html) for details.

`DJANGO_SETTINGS_MODULE` can be set to `argus.site.settings.dev`.

If you need more complex settings than environment variables and ``cmd.sh`` can provide,
we recommend having a `localsettings.py` in the same directory as `manage.py` with any
overrides.

Refer to the [development notes](http://argus-server.rtfd.io/en/latest/development.html) for further details and
useful hints on managing Argus in development mode.

### Step 3: Run Argus in development

Afterwards, run the initial Argus setup and start the server.
```console
$ python manage.py initial_setup
$ python manage.py runserver
```

You will find Argus running at http://localhost:8000/.

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
Refer to the [tox.ini](tox.ini) file for further options.
