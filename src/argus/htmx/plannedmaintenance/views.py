from django.contrib.auth.mixins import UserPassesTestMixin
from django.forms import modelform_factory
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from argus.htmx.utils import TemplateNameViewMixin
from argus.plannedmaintenance.models import PlannedMaintenanceTask


class UserIsStaffMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


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


class PlannedMaintenanceDeleteView(UserIsStaffMixin, PlannedMaintenanceMixin, DeleteView):
    pass


class PlannedMaintenanceCancelView(UserIsStaffMixin, PlannedMaintenanceMixin, DeleteView):
    http_method_names = ["post", "delete"]

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.cancel()
        return HttpResponseRedirect(success_url)


class PlannedMaintenanceCreateView(UserIsStaffMixin, PlannedMaintenanceMixin, CreateView):
    fields = ["start_time", "end_time", "description", "filters"]

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()
        return super().form_valid(form)


class PlannedMaintenanceUpdateView(UserIsStaffMixin, PlannedMaintenanceMixin, UpdateView):
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
