==================================
How to customize incident actions
==================================

When selecting one or more incidents in the incident list, a user gets the option to perform
one or more actions on those incidents. Currently, by default those actions are:

  * ack
  * close
  * reopen
  * update-ticket
  * add-ticket
  * autocreate-ticket

Customize an existing action
----------------------------

Now, say you want to customize how incidents are acknowledged, for example because you need
to perform additional logic. Also, you want users to acknowledge incidents without having to give
additional data such as a description or expiration date.

Let's first deal with the backend implementation. Argus has a registry of action handlers in the
form of a dictionary ``argus.htmx.incident.views.INCIDENT_UPDATE_ACTIONS``. This dictionary
contains a Form and a handling function for every action type. The Form is a ``django.forms.Form``
and the handlers are functions with the following signature::

  def action_handler(request: HtmxHttpRequest, qs: IncidentQuerySet, data: dict[str, Any]) -> Sequence[Incident]:
      """
      :param request: The django request that triggered the action
      :param qs: The queryset that contains all selected incidents
      :param data: a dictionary containing the Form's data
      :return: a sequence containing the incidents that have succesfully had the action applied
      """
      ...

For the backend, all you need to do is update the action handler for the ``ack`` action. Let's
assume that you have a custom action handler like this::

  def custom_ack_handler(request, qs, data):
      incidents = bulk_ack_queryset(request, qs, data) # the default behaviour
      ...  # add custom behaviour
      return incidents

You now need to register this handler. The best place to do this, is in your ``apps.py`` module in
the ``ready`` hook. This makes sure that the registration is always performed when your app is
loaded::

  class MyApp(AppConfig):
      ... # other stuff

      def ready(self):
          from argus.htmx.incident import views
          views.INCIDENT_UPDATE_ACTIONS['ack'] = (views.AckForm, custom_ack_handler)


Now, update the UI. The acknowledge button is rendered in the
``htmx/incident/_incident_acknowledge_modal.html`` template, in the htmx app template directory
``src/argus/htmx/templates``. This template renders a button that opens a modal with the form.
We want to update this behaviour so we won't have the form. The simplest way is to
:ref:`override<howto-override-templates>` the ``htmx/incident/_incident_acknowledge_modal.html``
template with the following content::

  <form id="{{ dialog_id }}-form"
        hx-post="{% url endpoint|default:'htmx:incident-update' action=action %}"
        hx-include="[name='incident_ids']"
        hx-indicator="#incident-list .htmx-indicator">
    {% csrf_token %}
    <input type='hidden' name='description' value='acknowledged through the ui'>
    <button type="submit" class="btn btn-accent">{{ button_title }}</button>
  </form>

Do note however, that there is now a mismatch in the template name, which still references a modal,
and the content of the template that now only has a button. For more fine grained control over
which templates to use to render buttons, please see the following sections that deal with removing
and adding actions

Adding a new action
-------------------

Adding a new action is similar to customizing an existing action. However, now you need to also
create a ``Form`` for the action and register it together with the action handler::

  # you can also place the form and handler in a different module
  class CustomActionForm(django.forms.Form):
      custom_field = django.forms.CharField()

  def custom_action_handler(request, qs, data):
      ...

  class MyApp(AppConfig):
      ... # other stuff

      def ready(self):
          from argus.htmx.incident import views
          views.INCIDENT_UPDATE_ACTIONS['custom-action'] = (CustomActionForm, custom_action_handler)


The UI part is also a little different. You need to override and extend the
``htmx/incident/_incident_list_update_menu.html`` template::

  {% extends "htmx/incident/_incident_list_update_menu.html" %}
  {% block update_menu_content %}
    {{ block.super }}
    {% with action_type="bulk-update" endpoint="htmx:incident-update" %}
      {% include "htmx/incident/_my_custom_action_modal.html" with action="my-custom-action" dialog_id="custom-action-dialog" button_class="btn-accent" button_title="Custom Action" header=Do a custom action" explanation="Write an URL of an existing ticket, or nothing to remove existing ticket URLs" cancel_text="Cancel" submit_text="Submit" %}

    {% endwith %}
  {% endblock update_menu_content %}

Create the following template ``htmx/incident/_my_custom_action_modal.html``::

  {% extends "htmx/incident/_base_incident_update_modal.html" %}
  {% block dialogform %}
    <label class="indicator input input-bordered flex items-center gap-2 w-full">
      Custom Field
      <span class="indicator-item indicator-top indicator-start badge border-none mask mask-circle text-warning text-base">＊</span>
      <input name="custom_field"
             autocomplete="off"
             type="text"
             placeholder="Custom placeholder"
             required
             class="appearance-none grow border-none" />
    </label>
  {% endblock dialogform %}


Removing an existing action
---------------------------

Removing an existing action involves removing the handler from the ``INCIDENT_UPDATE_ACTIONS``
registry and removing the button from the UI. For example, to remove the ``reopen`` action, place the
following in your ``apps.py``::

  class MyApp(AppConfig):
      ... # other stuff

      def ready(self):
          from argus.htmx.incident import views
          del views.INCIDENT_UPDATE_ACTIONS['reopen']

For the UI, you need to fully override the ``htmx/incident/_incident_list_update_menu.html``
template::

  <div class="menu menu-horizontal gap-2">
    {% block update_menu_content %}
      {% with action_type="bulk-update" endpoint="htmx:incident-update" %}
        {% include "htmx/incident/_incident_ticket_edit_modal.html" with action="update-ticket" dialog_id="add-ticket-dialog" button_class="btn-accent" button_title="Change ticket" header="Update ticket URL" explanation="Write an URL of an existing ticket, or nothing to remove existing ticket URLs" cancel_text="Cancel" submit_text="Submit" %}
        {% include "htmx/incident/_incident_acknowledge_modal.html" with action="ack" dialog_id="create-acknowledgment-dialog" button_class="btn-accent" button_title="Acknowledge" header="Submit acknowledgment" explanation="Write a message describing why these incidents were acknowledged" cancel_text="Cancel" submit_text="Submit" %}
        {% include "htmx/incident/_incident_close_modal.html" with action="close" dialog_id="close_incident-dialog" button_class="btn-accent" button_title="Close" header="Manually close incidents" explanation="Write a message describing why these incidents were manually closed" cancel_text="Cancel" submit_text="Close now" %}
      {% endwith %}
    {% endblock update_menu_content %}
  </div>
