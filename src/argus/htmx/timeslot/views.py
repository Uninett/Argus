from datetime import time
import logging
from typing import Optional

from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from argus.htmx.modals import DeleteModal
from argus.notificationprofile.models import Timeslot, TimeRecurrence


LOG = logging.getLogger(__name__)


class DaysMultipleChoiceField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple
    widget.option_template_name = "htmx/timeslot/checkbox_option.html"

    def to_python(self, value):
        value = super().to_python(value)
        return [int(day) for day in value]


class TimeRecurrenceForm(forms.ModelForm):
    days = DaysMultipleChoiceField()

    class Meta:
        TIMEINPUT_FORMAT = "%H:%M"
        TIMEINPUT_ATTRS = {
            "type": "text",
            "pattern": r"[012]\d:[0-5]\d",
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
        self.fields["days"].widget.attrs["class"] = "flex flex-row flex-wrap justify-between gap-2"
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


def make_timerecurrence_formset(data: Optional[dict] = None, timeslot: Optional[Timeslot] = None):
    extra = 1
    if not timeslot or not timeslot.time_recurrences.exists():
        extra = 0
    TimeRecurrenceFormSet = forms.inlineformset_factory(
        Timeslot,
        TimeRecurrence,
        form=TimeRecurrenceForm,
        fields="__all__",
        extra=extra,
        can_delete=True,
        min_num=1,
    )
    prefix = f"timerecurrenceform-{timeslot.pk}" if timeslot else ""
    TimeRecurrenceFormSet.template_name_div = "htmx/timeslot/timerecurrence_div.html"
    return TimeRecurrenceFormSet(data=data, instance=timeslot, prefix=prefix)


class TimeslotMixin:
    model = Timeslot
    prefix = "timeslot"

    def _get_prefix(self, pk):
        if pk:
            return self.prefix + f"-{pk}"
        return self.prefix

    def _set_delete_modal(self, form, obj):
        form.modal = DeleteModal(
            header="Delete timeslot",
            button_title="Delete timeslot",
            explanation=f'Delete the timeslot "{obj}"?',
            dialog_id=f"timeslot-delete-confirm-{obj.pk}",
            endpoint=reverse("htmx:timeslot-delete", kwargs={"pk": obj.pk}),
        )
        return form

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
            form = self._set_delete_modal(form, obj)
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
        form = context["form"]
        form = self._set_delete_modal(form, self.object)
        context["form"] = form
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
