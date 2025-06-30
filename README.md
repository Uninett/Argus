# Argus
[![test badge](https://github.com/Uninett/Argus/actions/workflows/python.yml/badge.svg)](https://github.com/Uninett/Argus/actions)
[![codecov badge](https://codecov.io/gh/Uninett/Argus/branch/master/graph/badge.svg)](https://codecov.io/gh/Uninett/Argus)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![djLint](https://img.shields.io/badge/html%20style-djlint-blue.svg)](https://www.djlint.com)
[![docs badge](https://readthedocs.org/projects/argus-server/badge/?version=latest&style=flat)](http://argus-server.rtfd.io/en/latest/)

Argus is a platform for aggregating incidents across network management systems, and
sending notifications to users. Users create notification profiles that define which
incidents they subscribe to. See [Argus docs](http://argus-server.rtfd.io/en/latest/) for more details.

See also the the [Python client library](https://github.com/Uninett/pyargus).

> [!IMPORTANT]
> * API v1 has been removed. API v2 is the new stable. Support for API v1
>   was dropped in version 2.0 of argus-server. Please upgrade your glue
>   services!
> * Support for the REACT frontend was dropped in version 2.0 of
>   argus-server. Please try out the new built-in one.


## Installation

There are several ways to install Argus.

### Prerequisites

#### Requirements

* Python 3.10+
* Django 5.2
* pip
* PostgreSQL 14+

#### Optional requirements

* Docker and Docker Compose to run Argus in Docker. This will also run
  a PostgreSQL server for you.

#### Optional: Frontend

You need to have the frontend-specific dependencies installed.

```
pip install argus-server[htmx]
```

will do it.

#### Optional: Federated login for frontend

See [Federated Login @ Read The Docs](https://argus-server.rtfd.io/en/latest/development/howtos/federated-logins.html) or [local copy of Federated Login docs](docs/development/howtos/federated-logins.rst).

### Install Argus using pip

You can also install Argus with `pip` via PyPI. The package name is `argus-server`:
```console
$ pip install argus-server
```

If you are using the PyPI package in production, please note: The file
`requirements.txt` contains the pinned versions of dependencies that the
release was tested on. The file `constraints.txt` is for controlling versions
of sub-dependencies so as to not poison the pyproject.toml.

To update the dependency lock-files, use `tox`:

```console
$ pip install "tox>=4"
$ tox run -e upgrade-deps -- -U
```

To upgrade a single dependency, replace the `-U` flag with `-P PACKAGENAME`.

To install from the lock-file use pip:

```console
$ pip install -c constraints.txt --upgrade -r requirements.txt
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

Running Argus with Docker Compose is as simple as
```console
$ docker compose up
```

Run the initial Argus setup, and make note of the admin password that is generated:

```console
$ docker compose exec api django-admin initial_setup
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
[site-specific settings](https://argus-server.readthedocs.io/en/latest/reference/site-specific-settings.html).


## Running Argus in development

### Step 1: Installation

You can use Docker Compose to conveniently setup a complete dev environment for Argus,
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
$ pip install -r requirements-django52.txt
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

`DJANGO_SETTINGS_MODULE` can be set to `argus.site.settings.dev`.

If you need more complex settings than environment variables and ``cmd.sh`` can provide,
we recommend having a `localsettings.py` in the same directory as `manage.py` with any
overrides.

Refer to the
[development notes](https://argus-server.readthedocs.io/en/latest/development.html)
for further details and useful hints on managing Argus in development mode.

#### Settings for the frontend

See https://argus-server.readthedocs.io/en/latest/reference/htmx-frontend.html.

### Step 3: Run Argus in development

Afterwards, run the initial Argus setup and start the server.
```console
$ python manage.py initial_setup
$ python manage.py runserver
```

You will find Argus running at http://localhost:8000/.

### Code style

Argus uses [ruff](https://docs.astral.sh/ruff/) as a Python source code
formatter and linter and [djLint](https://djlint.com/) as an HTML formatter and
linter. Ruff and djLint will automatically install with the
[dev requirements](requirements/dev.txt).

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

## Magical branches

Do not ever remove these

* master
* argus-demo
* stable/SOMETHING

The last branch-type is for backporting bugfixes and similar to older releases,
bypassing master if necessary.


## How to do maintenance

See [MAINTAINING.rst](MAINTAINING.rst).
