from __future__ import annotations

from datetime import time
import logging
from typing import Optional, TYPE_CHECKING

from django import forms
from django.contrib import messages
from django.forms.formsets import TOTAL_FORM_COUNT, INITIAL_FORM_COUNT
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from argus.htmx.widgets import BadgeDropdownMultiSelect
from argus.notificationprofile.models import Timeslot, TimeRecurrence

if TYPE_CHECKING:
    from django.http import QueryDict


LOG = logging.getLogger(__name__)
ADD_RECURRENCE = "add_recurrence"  # button name


class DaysMultipleChoiceField(forms.MultipleChoiceField):
    def to_python(self, value):
        value = super().to_python(value)
        return [int(day) for day in value]


class TimeRecurrenceForm(forms.ModelForm):
    days = DaysMultipleChoiceField()

    class Meta:
        TIMEINPUT_FORMAT = "%H:%M"
        TIMEINPUT_ATTRS = {
            "type": "text",
            "pattern": "[012]\d:[0-5]\d",
            "class": "input-bordered",
            "placeholder": "HH:MM",
        }

        model = TimeRecurrence
        exclude = ["timeslot"]
        widgets = {
            "start": forms.TimeInput(
                format=TIMEINPUT_FORMAT,
                attrs=TIMEINPUT_ATTRS,
            ),
            "end": forms.TimeInput(
                format=TIMEINPUT_FORMAT,
                attrs=TIMEINPUT_ATTRS,
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            partial_get = reverse(
                "htmx:timeslot-update",
                kwargs={"pk": self.instance.timeslot.id},
            )
        else:
            partial_get = reverse("htmx:timeslot-create")

        self.fields["days"].widget = BadgeDropdownMultiSelect(
            partial_get=partial_get,
            attrs={
                "placeholder": "select days...",
                "field_styles": "input input-bordered border-b max-w-full justify-center",
            },
        )
        self.fields["days"].choices = TimeRecurrence.Day.choices

    def clean_start(self):
        timeobj = self.cleaned_data["start"]
        timeobj = timeobj.replace(second=0, microsecond=0)
        return timeobj

    def clean_end(self):
        timeobj = self.cleaned_data["end"]
        max = time.max
        if timeobj.minute == max.minute:
            timeobj = timeobj.replace(second=max.second, microsecond=max.microsecond)
        else:
            timeobj = timeobj.replace(second=0, microsecond=0)
        return timeobj


class TimeslotForm(forms.ModelForm):
    class Meta:
        model = Timeslot
        fields = ["name"]


class InlineFormSet(forms.BaseInlineFormSet):
    template_name_div = "htmx/timeslot/timerecurrence_div.html"

    def _stored_total_form_count(self):
        return self.management_form.cleaned_data.get(TOTAL_FORM_COUNT, None)

    def _stored_initial_form_count(self):
        return self.management_form.cleaned_data.get(INITIAL_FORM_COUNT, None)

    def current_extra_form_count(self):
        return max(self._stored_total_form_count() - self._stored_initial_form_count(), 0)


def make_timerecurrence_formset(data: Optional[dict] = None, instance: Optional[Timeslot] = None, add: int = 0, **_):
    # we catch ``**_`` because get_form_kwargs may send in unused kwargs
    # e.g. "prefix", "initial"
    extra = 0 + max(add, 0)
    TimeRecurrenceFormSet = forms.inlineformset_factory(
        Timeslot,
        TimeRecurrence,
        form=TimeRecurrenceForm,
        formset=InlineFormSet,
        fields="__all__",
        extra=extra,
        can_delete=True,
        min_num=1,
    )
    prefix = f"timerecurrenceform-{instance.pk}" if instance else ""
    # keep in a variable for debugging purposes
    formset = TimeRecurrenceFormSet(data=data, instance=instance, prefix=prefix)
    print("Make: is bound:", formset.is_bound)
    print("Make: add", add, TimeRecurrenceFormSet.extra, formset.total_form_count(), len(formset.extra_forms))
    return formset


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
        context["add_recurrence_button_name"] = ADD_RECURRENCE
        return context


class FormsetMixin:
    def _must_add_form(self, data: Optional[QueryDict] = None):
        if not data:
            return False
        return bool(data.get(ADD_RECURRENCE, False))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()  # sets "data", "instance"
        if "data" in kwargs and self._must_add_form(kwargs["data"]):
            pass

        return kwargs

    def get_formset(self, must_add: bool = False):
        add = 0
        if must_add:
            # We need a formset instance in order to count the number of forms available
            formset = make_timerecurrence_formset(**self.get_form_kwargs())
            num_forms = formset.current_extra_form_count()
            add = num_forms + 1
        formset = make_timerecurrence_formset(**self.get_form_kwargs(), add=add)
        return formset

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        must_add = self._must_add_form(request.POST)
        formset = self.get_formset(must_add)
        if must_add:
            LOG.debug("Increment number of time recurrence forms and show them")
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        LOG.debug("Validating timeslot...")
        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_invalid(self, form, formset):
        errors = []
        for error in [form.errors] + formset.errors:
            if error:
                errors.append(error.as_text())
        if errors:
            messages.warning(self.request, f"Couldn't save timeslot: {errors}")
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def form_valid(self, form, formset):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        old_trs = self.object.time_recurrences.all()
        trs = formset.save(commit=False)
        for tr in trs:
            tr.timeslot = self.object
            tr.save()

        message_list = []
        timeslot_message = f"Set timeslot name to {self.object.name}."
        changed_message = f"Saved timeslot {self.object}."

        # bail out early if the only change is timeslot name
        if form.has_changed():
            if not (formset.changed_objects or formset.new_objects or formset.deleted_objects):
                messages.success(self.request, timeslot_message)
                return HttpResponseRedirect(self.get_success_url())

        if not old_trs.exists() and not len(trs):
            no_forms_msg = f'There are no time recurrences in timeslot "{self.object}". Click the "Delete"-button if you wish to delete the entire timeslot.'
            messages.warning(self.request, no_forms_msg)
            return HttpResponseRedirect(self.get_success_url())

        deleted = []
        for tr in formset.deleted_objects:
            deleted.append(str(tr))
            LOG.debug("Delete %s (%s)", tr, tr.id)
            tr.delete()
        if deleted:
            delete_message = "Deleted " + ", ".join(deleted) + f" from {self.object}."
            message_list.append(delete_message)

        if formset.new_objects:
            new_message = f"Added time recurrence to timeslot {self.object}."
            message_list.append(new_message)
            for new_tr in formset.new_objects:
                LOG.debug("Add %s", new_tr)

        if form.has_changed() or formset.changed_objects:
            message_list.append(changed_message)
            for changed_tr, changed in formset.changed_objects:
                LOG.debug("Update %s (%s), %s", changed_tr, changed_tr.id, changed)

        if message_list:
            message = " ".join(message_list)
            LOG.info(message)
            messages.success(self.request, message)
        return HttpResponseRedirect(self.get_success_url())


class TimeslotListView(TimeslotMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forms = []
        for obj in self.get_queryset():
            form = TimeslotForm(None, instance=obj, prefix=self._get_prefix(obj.pk))
            formset = make_timerecurrence_formset(instance=obj)
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
        data = self.get_form_kwargs().get("data", None)
        must_add = self._must_add_form(data)
        formset = self.get_formset(must_add)
        context["formset"] = formset
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)


class TimeslotUpdateView(FormsetMixin, TimeslotMixin, UpdateView):
    fields = ["name"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.get_form_kwargs().get("data", None)
        must_add = self._must_add_form(data)
        formset = self.get_formset(must_add)
        context["formset"] = formset
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)


class TimeslotDeleteView(TimeslotMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'Successfully deleted timeslot "{self.object}"')
        return HttpResponseRedirect(success_url)
