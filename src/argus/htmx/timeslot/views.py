from typing import Optional

from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from argus.notificationprofile.models import Timeslot, TimeRecurrence


class TimeRecurrenceForm(forms.ModelForm):
    class Meta:
        model = TimeRecurrence
        exclude = ["timeslot"]
        widgets = {
            "start": forms.TimeInput(
                attrs={
                    "type": "text",
                    "pattern": "[0-2][0-9]:[0-5][0-9]",
                    "class": "input-bordered",
                }
            ),
            "end": forms.TimeInput(
                attrs={
                    "type": "time",
                    "step": 60,
                    "class": "input-bordered",
                }
            ),
        }


class TimeslotForm(forms.ModelForm):
    class Meta:
        model = Timeslot
        fields = ["name"]


def make_timerecurrence_formset(data: Optional[dict] = None, timeslot: Optional[Timeslot] = None):
    extra = 0 if not timeslot else 1
    TimeRecurrenceFormSet = forms.inlineformset_factory(
        Timeslot, TimeRecurrence, form=TimeRecurrenceForm, fields="__all__", extra=extra, can_delete=False, min_num=1
    )
    prefix = f"timerecurrenceform-{timeslot.pk}" if timeslot else ""
    return TimeRecurrenceFormSet(data=data, instance=timeslot, prefix=prefix)


class TimeslotMixin:
    model = Timeslot
    prefix = "timeslot"

    def _get_prefix(self, pk):
        if pk:
            return self.prefix + f"-{pk}"
        return self.prefix

    def get_prefix(self):
        return self._get_prefix(getattr(self.object, "pk", None))

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Timeslots"
        return context


class FormsetMixin:
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = make_timerecurrence_formset(data=request.POST, timeslot=self.object)
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_invalid(self, form, formset):
        errors = []
        for error in [form.errors] + formset.errors:
            if error:
                errors.append(error.as_text())
        messages.warning(self.request, f"Couldn't save timeslot: {errors}")
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def form_valid(self, form, formset):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        trs = formset.save(commit=False)
        for tr in trs:
            tr.timeslot = self.object
            tr.save()
        messages.success(self.request, f"Saved timeslot {self.object}")
        return HttpResponseRedirect(self.get_success_url())


class TimeslotListView(TimeslotMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forms = []
        for obj in self.get_queryset():
            form = TimeslotForm(None, instance=obj, prefix=self._get_prefix(obj.pk))
            formset = make_timerecurrence_formset(timeslot=obj)
            forms.append({"form": form, "formset": formset})
        context["form_list"] = forms
        return context


class TimeslotDetailView(TimeslotMixin, DetailView):
    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        return redirect("htmx:timeslot-update", pk=object.pk)


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
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'Successfully deleted timeslot "{self.object}"')
        return HttpResponseRedirect(success_url)
