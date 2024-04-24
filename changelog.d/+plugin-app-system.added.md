Added simple support for pluggable django-apps. The setting `EXTENSION_APPS` is
loaded first in `INSTALLED_APPS` and `urls.py`, and can override templates and
views. The setting `EXTRA_APPS` is safer, it is loaded last in `INSTALLED_APPS`
and `urls.py` and can therefore only add additional templates and views.
