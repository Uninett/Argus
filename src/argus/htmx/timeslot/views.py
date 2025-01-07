from typing import Optional

from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from argus.notificationprofile.models import Timeslot, TimeRecurrence


class TimeRecurrenceForm(forms.ModelForm):
    class Meta:
        model = TimeRecurrence
        exclude = ["timeslot"]


def make_timerecurrence_formset(data: Optional[dict] = None, timeslot: Optional[Timeslot] = None):
    extra = 0 if not timeslot else 1
    TimeRecurrenceFormSet = forms.inlineformset_factory(
        Timeslot, TimeRecurrence, fields="__all__", extra=extra, can_delete=False, min_num=1
    )
    return TimeRecurrenceFormSet(data=data, instance=timeslot)


class TimeslotMixin:
    model = Timeslot

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related("time_recurrences")
        return qs.filter(user_id=self.request.user.id)

    def get_template_names(self):
        orig_app_label = self.model._meta.app_label
        orig_model_name = self.model._meta.model_name
        self.model._meta.app_label = "htmx/timeslot"
        self.model._meta.model_name = "timeslot"
        templates = super().get_template_names()
        self.model._meta.app_label = orig_app_label
        self.model._meta.model_name = orig_model_name
        return templates

    def get_success_url(self):
        return reverse("htmx:timeslot-list")


class FormsetMixin:
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = make_timerecurrence_formset(data=request.POST, timeslot=self.object)
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_invalid(self, form, formset):
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def form_valid(self, form, formset):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        trs = formset.save(commit=False)
        for tr in trs:
            tr.timeslot = self.object
            tr.save()
        return HttpResponseRedirect(self.get_success_url())


class TimeslotListView(TimeslotMixin, ListView):
    pass


class TimeslotDetailView(TimeslotMixin, DetailView):
    pass


class TimeslotCreateView(FormsetMixin, TimeslotMixin, CreateView):
    fields = ["name"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = make_timerecurrence_formset()
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)


class TimeslotUpdateView(FormsetMixin, TimeslotMixin, UpdateView):
    fields = ["name"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["formset"] = make_timerecurrence_formset(timeslot=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)


class TimeslotDeleteView(TimeslotMixin, DeleteView):
    pass
