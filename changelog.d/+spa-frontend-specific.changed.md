Split out all the hard coded support for the REACT SPA frontend into a library.

In the process, the following renames were done:

- `ARGUS_COOKIE_DOMAIN` -> `ARGUS_SPA_COOKIE_DOMAIN`
- `COOKIE_DOMAIN` -> `SPA_COOKIE_DOMAIN`
- `ARGUS_TOKEN_COOKIE_NAME` -> `ARGUS_SPA_TOKEN_COOKIE_NAME`

How to deploy with support for this backend has also changed, see the new
documentation section REACT Frontend. In short, it is necessary to change which
settings-file to base the deployment on.
