from datetime import time
import logging
from typing import Optional

from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django_htmx.http import HttpResponseClientRedirect

from argus.htmx.modals import DeleteModal
from argus.notificationprofile.models import Timeslot, TimeRecurrence


LOG = logging.getLogger(__name__)


class DaysMultipleChoiceField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple

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
        self.fields["days"].widget.attrs["class"] = "flex flex-row gap-1"
        self.fields["days"].choices = [(day.value, day.label[0]) for day in TimeRecurrence.Day]

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

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        if start and end and start >= end:
            self.add_error("start", "Start time must be before end time.")
        return cleaned_data


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
    prefix = f"timerecurrenceform-{timeslot.pk}" if timeslot else "timerecurrenceform"
    TimeRecurrenceFormSet.template_name_div = "htmx/timeslot/timerecurrence_div.html"
    return TimeRecurrenceFormSet(data=data, instance=timeslot, prefix=prefix)


class TimeslotMixin:
    model = Timeslot
    prefix = "timeslot"

    def _get_prefix(self, pk):
        if pk:
            return self.prefix + f"-{pk}"
        return self.prefix

    def _make_delete_modal(self, obj, **kwargs):
        return DeleteModal(
            header="Delete timeslot",
            button_title="Delete",
            button_class="btn-sm btn-outline btn-error",
            explanation=f'Delete the timeslot "{obj}"?',
            dialog_id=f"timeslot-delete-confirm-{obj.pk}",
            endpoint=reverse("htmx:timeslot-delete", kwargs={"pk": obj.pk}),
            **kwargs,
        )

    def _set_delete_modal(self, form, obj):
        form.modal = self._make_delete_modal(obj)
        return form

    def _attach_card_delete_modal(self, obj):
        obj.delete_modal = self._make_delete_modal(obj, opener_button_template_name="htmx/_blank.html")

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
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def form_valid(self, form, formset):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        trs = formset.save(commit=False)
        for tr in trs:
            tr.timeslot = self.object
            tr.save()

        message_list = []
        changed_message = f"Saved timeslot {self.object}."

        # bail out early if the only change is timeslot name
        if form.has_changed():
            if not (formset.changed_objects or formset.new_objects or formset.deleted_objects):
                return self.form_valid_response()

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

        # Warn if timeslot ends up with no recurrences after all changes
        self.object.refresh_from_db()
        if not self.object.time_recurrences.exists():
            no_forms_msg = f'There are no time recurrences in timeslot "{self.object}". Click the "Delete"-button if you wish to delete the entire timeslot.'
            messages.warning(self.request, no_forms_msg)

        if message_list:
            message = " ".join(message_list)
            LOG.info(message)

        return self.form_valid_response()


class TimeslotListView(TimeslotMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for obj in context["object_list"]:
            self._attach_card_delete_modal(obj)
        return context


class TimeslotDetailView(TimeslotMixin, DetailView):
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.htmx:
            self._attach_card_delete_modal(obj)
            return TemplateResponse(
                request,
                "htmx/timeslot/_timeslot_card.html",
                {"timeslot": obj},
            )
        return redirect("htmx:timeslot-update", pk=obj.pk)


class TimeslotCreateView(FormsetMixin, TimeslotMixin, CreateView):
    fields = ["name"]

    def get_template_names(self):
        if self.request.htmx:
            return ["htmx/timeslot/_timeslot_form.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "formset" not in context:
            context["formset"] = make_timerecurrence_formset()
        context["is_create"] = True
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)

    def form_valid_response(self):
        if self.request.htmx:
            return HttpResponseClientRedirect(self.get_success_url())
        return HttpResponseRedirect(self.get_success_url())


class TimeslotUpdateView(FormsetMixin, TimeslotMixin, UpdateView):
    fields = ["name"]

    def get_template_names(self):
        if self.request.htmx:
            return ["htmx/timeslot/_timeslot_form_content.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "formset" not in context:
            context["formset"] = make_timerecurrence_formset(timeslot=self.object)
        form = context["form"]
        form = self._set_delete_modal(form, self.object)
        context["form"] = form
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid_response(self):
        if self.request.htmx:
            context = self.get_context_data()
            context["timeslot"] = self.object
            now = timezone.localtime().strftime("%H:%M:%S")
            context["success_message"] = f'Saved timeslot "{self.object}" at {now}'
            return self.render_to_response(context)
        return HttpResponseRedirect(self.get_success_url())


class TimeslotDeleteView(TimeslotMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        if request.htmx:
            return HttpResponseClientRedirect(success_url)
        return HttpResponseRedirect(success_url)
