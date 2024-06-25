Move filter stuff to new app, argus.filter

* Move Filter-dependent methods out of incident/models.py
* Move filter settings check to argus.filter
* Keep OpenAPI queryparam descriptions with their filters in argus.filter.filters
* Update and improve tests
* Move Filter `*_fits` methods to FilterWrapper
* Move NotificationProfile `*_fits` methods to ComplexFilterWrapper
* Add docstring to argus.filter.filter
* Simplify/DRY existing filterwrapper methods, including tristate
