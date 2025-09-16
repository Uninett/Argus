# Docker production image of Argus

Whereas the top-level Dockerfile is development-oriented, this directory
contains definitions to build a production-oriented Docker image of the Argus
API backend component.

To build this image, the build context needs to be that of the git repository
root. Something like this would work (when the current working directory is
here):

```shell
docker build -t argus -f Dockerfile ..
```

Or, from the top level directory:

```shell
docker build -t argus -f docker/Dockerfile .
```

## Configuration of the running container

This image runs with default production settings, with a few tweaks from
[dockersettings.py](dockersettings.py). The most useful settings can be
overriden through the use of environment variables exported to the container,
but some MUST be set.

The required environment variables in question are:

* `ARGUS_FRONTEND_URL` (url)
* `DATABASE_URL` (example: postgresql://argus:PASSWORD@HOST.NAME:5432/argus)
* `DEFAULT_FROM_EMAIL` (email address)
* `EMAIL_HOST` (hostname or ip address)
* `SECRET_KEY` (long random string, around 50 characters is good)

The `SECRET_KEY` and `DATABASE_URL` should be protected from prying eyes.

Consult the documentation section on [site-specific
settings](http://argus-server.rtfd.io/en/latest/site-specific-settings.html).
for further details.

## Limitations

This is not a complete Argus environment.  This image only defines the web
server component: API and frontend. It still depends on a PostgreSQL server to
be functional.

For a full production environment example, take a look at
https://github.com/Uninett/argus-docker
