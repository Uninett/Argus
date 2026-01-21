from datetime import timedelta

from django import forms
from django.contrib.auth.mixins import UserPassesTestMixin
from django.forms import modelform_factory
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from argus.htmx.utils import TemplateNameViewMixin
from argus.htmx.widgets import SearchDropdownMultiSelect
from argus.notificationprofile.models import Filter
from argus.plannedmaintenance.models import PlannedMaintenanceTask

FLATPICKR_DATETIME_FORMAT = "%Y-%m-%d %H:%M"


class UserIsStaffMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class PlannedMaintenanceMixin(TemplateNameViewMixin):
    model = PlannedMaintenanceTask
    template_name_piece = "plannedmaintenance"

    def get_success_url(self):
        return reverse("htmx:plannedmaintenance-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Planned Maintenance"
        return context


class PlannedMaintenanceListView(PlannedMaintenanceMixin, ListView):
    tab = "upcoming"

    def get_tab(self):
        return self.kwargs.get("tab") or self.tab

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_tab"] = self.get_tab()
        return context

    def get_queryset(self):
        qs = PlannedMaintenanceTask.objects.all()
        if self.get_tab() == "past":
            return qs.past().order_by("-end_time")
        else:
            # Upcoming = ongoing + future, ordered by start_time
            return (qs.current() | qs.future()).order_by("start_time")


class PlannedMaintenanceDeleteView(UserIsStaffMixin, PlannedMaintenanceMixin, DeleteView):
    pass


class PlannedMaintenanceCancelView(UserIsStaffMixin, PlannedMaintenanceMixin, DeleteView):
    http_method_names = ["post", "delete"]

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.cancel()
        return HttpResponseRedirect(success_url)


class FilterWidgetMixin:
    """Mixin to configure the filters field with SearchDropdownMultiSelect widget."""

    def get_filter_widget(self):
        return SearchDropdownMultiSelect(
            partial_get=reverse("htmx:search-filters"),
            attrs={"placeholder": "Search by filter name or username..."},
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if "filters" in form.fields:
            form.fields["filters"].queryset = Filter.objects.select_related("user")
            form.fields["filters"].label_from_instance = lambda obj: f"{obj.name} ({obj.user.username})"
        return form


class PlannedMaintenanceCreateView(UserIsStaffMixin, FilterWidgetMixin, PlannedMaintenanceMixin, CreateView):
    fields = ["start_time", "end_time", "description", "filters"]

    def get_form_class(self):
        return modelform_factory(
            self.model,
            fields=self.fields,
            widgets={
                "start_time": forms.DateTimeInput(
                    attrs={"class": "flatpickr-datetime"}, format=FLATPICKR_DATETIME_FORMAT
                ),
                "end_time": forms.DateTimeInput(
                    attrs={"class": "flatpickr-datetime"}, format=FLATPICKR_DATETIME_FORMAT
                ),
                "filters": self.get_filter_widget(),
            },
        )

    def get_initial(self):
        initial = super().get_initial()
        now = timezone.now()
        initial["start_time"] = now
        initial["end_time"] = now + timedelta(hours=1)
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class PlannedMaintenanceDetailView(PlannedMaintenanceMixin, DetailView):
    """Read-only view for viewing maintenance tasks."""

    template_name = "htmx/plannedmaintenance/plannedmaintenance_form.html"


class PlannedMaintenanceUpdateView(UserIsStaffMixin, FilterWidgetMixin, PlannedMaintenanceMixin, UpdateView):
    fields = ["start_time", "end_time", "description", "filters"]
    future_fields = fields
    ongoing_fields = ["end_time", "description", "filters"]

    def get_form_class(self):
        obj = self.get_object()
        if obj.current:
            fields = self.ongoing_fields
        else:
            fields = self.future_fields

        widgets = {}
        if "start_time" in fields:
            widgets["start_time"] = forms.DateTimeInput(
                attrs={"class": "flatpickr-datetime"}, format=FLATPICKR_DATETIME_FORMAT
            )
        if "end_time" in fields:
            widgets["end_time"] = forms.DateTimeInput(
                attrs={"class": "flatpickr-datetime"}, format=FLATPICKR_DATETIME_FORMAT
            )
        if "filters" in fields:
            widgets["filters"] = self.get_filter_widget()

        return modelform_factory(self.model, fields=fields, widgets=widgets)
