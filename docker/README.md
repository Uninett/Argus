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

## Services

While this image provides the necessary environment for the backend processes,
it defaults to run only the API server itself.  In addition to an API
container, a second container is needed to process notifications
asynchronously.  The second container needs to run from this same image, but
you should replace the container command with `django-admin qcluster`, to run
the "qcluster" service.

The "qcluster" command comes from Django Q2, and is used to process a message
queue of tasks to complete in the background.

## Configuration of the running containers

This image runs with default production settings, with a few tweaks from
[dockersettings.py](dockersettings.py). This means that the most useful
settings can be overriden through the use of environment variables exported to
the container.  Consult the documentation section on [site-specific
settings](http://argus-server.rtfd.io/en/latest/site-specific-settings.html).

## Limitations

This is not a complete Argus environment.  This image only defines the backend
API server component. It still depends on a PostgreSQL and a Redis server to be
functional. Also, the Argus front-end component is needed to have a functional
user interface against the API server.

For a full production environment example, take a look at
https://github.com/Uninett/argus-docker
