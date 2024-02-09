Add two development dependencies

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
