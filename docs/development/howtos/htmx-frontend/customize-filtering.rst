=============================================
How to customize filtering the incidents list
=============================================

Incident list filtering is governed by the ``incident_list_filter`` function. By default, this
function is located at ``argus.htmx.incidents.filter.incident_list_filter`` but this location
can be changed by overriding the ``ARGUS_HTMX_FILTER_FUNCTION`` to point to a different function.
The function has the the following signature::

  def incident_list_filter(request: HttpRequest, qs: IncidentQuerySet, use_empty_filter: bool = False) -> tuple[Form, IncidentQuerySet]:
      ...

The ``ARGUS_HTMX_FILTER_FUNCTION`` can either take a function directly or a dotted path to an
importable function. For backwards compatibility, it is also possible to specify a dotted path
to a module instead of a function. Argus will then look for a function called
``incident_list_filter`` inside that module.

When loading the incidents list, the incident_list_filter function is called with the request and
the base incident queryset, and allows for updating this queryset. This way, the queryset can for
example be filtered, reordered and/or data may be added (such as through ``annotate``).
It is also possible to specify whether the default (empty) filter should be used or not.

Aside from the updated queryset, ``incident_list_filter`` returns a ``django.forms.Form``. This
form is used to populate the incident filterbox and any filterable columns

Filterable columns
------------------

Argus has support for applying filters directly on the incident list column header. To do this, for
example to allow the filtering "Description" column, add/update the ``IncidentTableColumn`` in your
``INCIDENT_TABLE_COLUMN`` setting::

  INCIDENT_TABLE_COLUMNS = [
    ...
    IncidentTableColumn(
        "description",
        label="Description",
        cell_template="htmx/incident/cells/_incident_description.html",
        filter_field="description",
    ),
    ...
  ]

You then need to update your ``incident_list_filter`` ``Form`` to something akin to the following::

  class IncidentFilterForm(forms.Form):
      ...
      description = forms.CharField(max_length=255, required=False)
      description.in_header = True
      ...

The attribute name ``description`` should match the value of the
``IncidentTableColumn.filter_field`` attribute. This will tell argus_htmx to not render a filter
input for the description in the incident filter box, but to use the column header filter instead
