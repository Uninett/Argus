from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django_htmx.http import HttpResponseClientRedirect

from argus.htmx.modals import DeleteModal
from argus.notificationprofile.models import DestinationConfig
from argus.notificationprofile.media import api_safely_get_medium_object
from argus.notificationprofile.media.base import NotificationMedium

from .forms import DestinationFormCreate, DestinationFormUpdate


DESTINATION_TABLE_TEMPLATE = "htmx/destination/_destination_table.html"


def _attach_delete_state(form, make_modal):
    """Attach delete modal or disabled state to a form based on deletability.

    Note: DestinationFormUpdate.__init__ mutates instance.settings from a dict
    to a plain string, so we read the raw settings from DB for the synced check.
    """
    destination = form.instance
    in_use = destination.notification_profiles.exists()
    raw_settings = DestinationConfig.objects.values_list("settings", flat=True).get(pk=destination.pk)
    synced = raw_settings.get("synced", False) if isinstance(raw_settings, dict) else False

    if in_use:
        form.delete_disabled = True
        form.delete_tooltip = "This destination is used by a notification profile and cannot be deleted"
    elif synced:
        form.delete_disabled = True
        form.delete_tooltip = "This destination is synced from an outside source and cannot be deleted"
    else:
        form.delete_disabled = False
        form.modal = make_modal(destination)


class DestinationMixin:
    model = DestinationConfig
    prefix = "destination"

    def _get_prefix(self, pk):
        if pk:
            return f"{self.prefix}_{pk}"
        return self.prefix

    def _make_delete_modal(self, obj, **kwargs):
        return DeleteModal(
            header="Delete destination",
            button_title="Delete",
            button_class="btn-sm btn-outline btn-error",
            explanation=f'Delete the destination "{obj.label or obj.pk}"?',
            dialog_id=f"destination-delete-confirm-{obj.pk}",
            endpoint=reverse("htmx:destination-delete", kwargs={"pk": obj.pk}),
            **kwargs,
        )

    def get_prefix(self):
        return self._get_prefix(getattr(self.object, "pk", None))

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user).order_by("pk")

    def get_template_names(self):
        return [f"htmx/destination/destination{self.template_name_suffix}.html"]

    def get_success_url(self):
        return reverse("htmx:destination-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Destinations"
        context["active_tab"] = "destinations"
        return context


class DestinationListView(DestinationMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        update_forms = _get_update_forms(self.request.user)
        for f in update_forms:
            _attach_delete_state(f, self._make_delete_modal)
        context["update_forms"] = update_forms
        return context


class DestinationCreateView(DestinationMixin, CreateView):
    form_class = DestinationFormCreate
    htmx_template = "htmx/destination/_destination_create_row.html"

    def get_template_names(self):
        if self.request.htmx:
            return [self.htmx_template]
        return super().get_template_names()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        form.save()
        if self.request.htmx:
            return HttpResponseClientRedirect(self.get_success_url())
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if self.request.htmx:
            return TemplateResponse(
                self.request,
                self.htmx_template,
                {"form": form},
            )
        return super().form_invalid(form)


class DestinationUpdateView(DestinationMixin, UpdateView):
    form_class = DestinationFormUpdate

    def get_prefix(self):
        return self._get_prefix(self.object.pk)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset)
        return self.object

    def form_valid(self, form):
        form.save()
        return self._render_table(
            success_message=f"Saved destination at {timezone.localtime().strftime('%H:%M:%S')}.",
        )

    def form_invalid(self, form):
        update_forms = _get_update_forms(self.request.user)
        update_forms = _replace_form_in_list(update_forms, form)
        for f in update_forms:
            _attach_delete_state(f, self._make_delete_modal)
        context = {"update_forms": update_forms}
        return TemplateResponse(
            self.request,
            DESTINATION_TABLE_TEMPLATE,
            context,
        )

    def _render_table(self, error_msg=None, success_message=None):
        update_forms = _get_update_forms(self.request.user)
        for f in update_forms:
            _attach_delete_state(f, self._make_delete_modal)
        context = {
            "update_forms": update_forms,
            "error_msg": error_msg,
            "success_message": success_message,
        }
        return TemplateResponse(
            self.request,
            DESTINATION_TABLE_TEMPLATE,
            context,
        )


class DestinationDeleteView(DestinationMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            medium = api_safely_get_medium_object(self.object.media.slug)
            medium.raise_if_not_deletable(self.object)
        except NotificationMedium.NotDeletableError as e:
            update_forms = _get_update_forms(request.user)
            for f in update_forms:
                _attach_delete_state(f, self._make_delete_modal)
            response = TemplateResponse(
                request,
                DESTINATION_TABLE_TEMPLATE,
                {
                    "update_forms": update_forms,
                    "error_msg": " ".join(e.args),
                },
            )
            response["HX-Retarget"] = "#destination-table"
            response["HX-Reswap"] = "outerHTML"
            return response
        else:
            self.object.delete()
        return HttpResponseRedirect(self.get_success_url())


def _get_update_forms(user) -> list[DestinationFormUpdate]:
    destinations = user.destinations.all().order_by("pk")
    return [
        DestinationFormUpdate(instance=destination, prefix=f"destination_{destination.pk}")
        for destination in destinations
    ]


def _replace_form_in_list(forms: list[DestinationFormUpdate], form: DestinationFormUpdate):
    for index, f in enumerate(forms):
        if f.instance.pk == form.instance.pk:
            forms[index] = form
            break
    return forms
