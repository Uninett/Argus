==========================
How to customize filtering
==========================

The public interface is in ``argus.filter.defaults``. How to structure the code
that does the actual filtering is an implementation detail, as long as it
exposes the names defined there.

The optional setting ``ARGUS_FILTER_BACKEND`` defaults to
``"argus.filter.defaults"``, change it to point to your own dotted path to
a module exposing the same names as ``argus.filter.defaults``.

Contents of ``argus.filter.defaults``
=====================================

Everything is based around the "filterblob", a JSON structure.

-----------------------------------------
Matching one incident to multiple filters
-----------------------------------------

This is currently used to decide whether to send notifications for new and
changed incidents.

FilterWrapper
-------------

Base class, the important methods are ``incident_fits`` and ``event_fits``.

FallbackFilterWrapper
---------------------

Subclass of ``FilterWrapper``. Merges a filter with the filter in the setting
``ARGUS_FALLBACK_FILTER``.

ComplexFilterWrapper
--------------------

OR's together multiple simple FilterWrappers, used by NotificationProfile.

ComplexFallbackFilterWrapper
----------------------------

Subclass of ``FilterWrapper``. Takes the setting ``ARGUS_FALLBACK_FILTER`` into
account for each filter.

---------------------------------------
Matching a filter to multiple incidents
---------------------------------------

Used by the bulk management command.

QuerySetFilter
--------------

The class is used to bundle public functions together, no initializing necessary.

The most important method is ``filtered_incidents``, which given a filterblob spits
out a queryset of incidents that fit that filter.

In addition there are the helper methods ``incidents_by_*`` which runs
``filtered_incidents`` on the actual ``Filter`` and ``NotificationProfile``
models.

------------------
API GET-parameters
------------------

IncidentFilter
--------------

django-filters backend that translates GET-parameters to an Incident queryset
fitting those paramterers.

SourceLockedIncidentFilter
--------------------------

Identical to ``IncidentFilter`` except the ``source*``-parameters are not
included. This is for a source filtering on its own incidents.

INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS
---------------------------------------

OpenAPI spec for IncidentFilter. Depends on drf-spectacular.

SOURCE_LOCKED_INCIDENT_OPENAPI_PARAMETER_DESCRIPTIONS
-----------------------------------------------------

OpenAPI spec for SourceLockedIncidentFilter. Depends on drf-spectacular.

-----------
Serializers
-----------

This is how you validate the filterblob. Depends on ``django-rest-framework``.

FilterSerializer
----------------

Validates the data of a Filter model instance. Depends on ``FilterBlobSerializer``.

FilterBlobSerializer
--------------------

Validates the actual filterblob. This is what everything else depends on. Currently of the format

::

    {
        "key1": "value1"
        "key2": ["value1", "value2"]
    }

----------
Validators
----------

validate_jsonfilter
-------------------

Runs a ``FilterBlobSerializer`` on something assumed to be a filterblob and returns
``True`` if it is a valid filterblob. Raises a ``ValidationError`` with error
details otherwise. Depends on ``django-rest-framework``.
