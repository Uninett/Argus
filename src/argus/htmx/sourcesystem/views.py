from django.contrib import messages
from django.db.models import Count, ProtectedError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from argus.htmx.plannedmaintenance.views import UserIsStaffMixin
from argus.htmx.utils import TemplateNameViewMixin
from argus.incident.models import SourceSystem, SourceSystemType

from .forms import AddSourceSystemTypeForm, CreateSourceSystemForm, UpdateSourceSystemForm


class SourceSystemMixin(TemplateNameViewMixin):
    model = SourceSystem
    template_name_piece = "sourcesystem"

    def get_success_url(self):
        return reverse("htmx:sourcesystem-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sources"
        context["active_tab"] = "sources"
        return context


class SourceSystemTypeMixin(TemplateNameViewMixin):
    model = SourceSystemType
    template_name_piece = "sourcesystem"

    def get_success_url(self):
        return reverse("htmx:sourcesystemtype-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sources"
        context["active_tab"] = "types"
        return context


class SourceSystemListView(SourceSystemMixin, ListView):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("type", "user")
            .annotate(incident_count=Count("incidents"))
            .order_by("name")
        )


class SourceSystemCreateView(UserIsStaffMixin, SourceSystemMixin, CreateView):
    form_class = CreateSourceSystemForm


class SourceSystemUpdateView(UserIsStaffMixin, SourceSystemMixin, UpdateView):
    form_class = UpdateSourceSystemForm


class ProtectedDeleteMixin:
    protected_error_message = 'Cannot delete "{object}".'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(request, self.protected_error_message.format(object=self.object))
        return HttpResponseRedirect(self.get_success_url())


class SourceSystemDeleteView(UserIsStaffMixin, SourceSystemMixin, ProtectedDeleteMixin, DeleteView):
    protected_error_message = 'Cannot delete source "{object}" because it has associated incidents.'


class SourceSystemTypeListView(SourceSystemTypeMixin, ListView):
    def get_queryset(self):
        return SourceSystemType.objects.annotate(source_count=Count("instances")).order_by("name")

    def get_template_names(self):
        return ["htmx/sourcesystem/sourcesystemtype_list.html"]


class SourceSystemTypeCreateView(UserIsStaffMixin, SourceSystemTypeMixin, CreateView):
    form_class = AddSourceSystemTypeForm

    def get_template_names(self):
        return ["htmx/sourcesystem/sourcesystemtype_form.html"]


class SourceSystemTypeDeleteView(UserIsStaffMixin, SourceSystemTypeMixin, ProtectedDeleteMixin, DeleteView):
    protected_error_message = 'Cannot delete type "{object}" because it has associated source systems.'
