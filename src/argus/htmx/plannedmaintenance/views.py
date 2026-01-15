from django.forms import modelform_factory
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from argus.htmx.utils import TemplateNameViewMixin
from argus.plannedmaintenance.models import PlannedMaintenanceTask


class PlannedMaintenanceMixin(TemplateNameViewMixin):
    model = PlannedMaintenanceTask
    template_name_piece = "plannedmaintenance"
    prefix = template_name_piece

    def get_success_url(self):
        return reverse("htmx:plannedmaintenance-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Planned Maintenance Tasks"
        return context


class PlannedMaintenanceListView(PlannedMaintenanceMixin, ListView):
    pass


class PlannedMaintenanceDeleteView(PlannedMaintenanceMixin, DeleteView):
    pass


class PlannedMaintenanceCreateView(PlannedMaintenanceMixin, CreateView):
    fields = ["start_time", "end_time", "description", "filters"]

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()
        return super().form_valid(form)


class PlannedMaintenanceUpdateView(PlannedMaintenanceMixin, UpdateView):
    fields = ["start_time", "end_time", "description", "filters"]
    future_fields = fields
    ongoing_fields = ["end_time", "description", "filters"]
    past_fields = ["description"]

    def get_form_class(self):
        object = self.get_object()
        if object.past:
            fields = self.past_fields
        elif object.current:
            fields = self.ongoing_fields
        else:
            fields = self.future_fields
        form_class = modelform_factory(self.model, fields=fields)
        return form_class


@require_http_methods(["POST"])
def cancel_planned_maintenance(request, pk: int):
    pm = get_object_or_404(PlannedMaintenanceTask, pk=pk)
    pm.cancel()
    return redirect(reverse("htmx:plannedmaintenance-list"))
