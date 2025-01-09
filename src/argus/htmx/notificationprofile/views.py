"""
Everything needed python-wise to CRUD notificationprofiles

See https://ccbv.co.uk/ to grok class-based views.
"""

from django import forms
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from argus.htmx.request import HtmxHttpRequest
from argus.htmx.widgets import DropdownMultiSelect
from argus.notificationprofile.media import MEDIA_CLASSES_DICT
from argus.notificationprofile.models import NotificationProfile, Timeslot, Filter, DestinationConfig


class NoColonMixin:
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)


class DestinationFieldMixin:
    def _get_destination_choices(self, user):
        choices = []
        for dc in DestinationConfig.objects.filter(user=user):
            MediaPlugin = MEDIA_CLASSES_DICT[dc.media.slug]
            label = MediaPlugin.get_label(dc)
            choices.append((dc.id, f"{dc.media.name}: {label}"))
        return choices


class NotificationProfileForm(DestinationFieldMixin, NoColonMixin, forms.ModelForm):
    class Meta:
        model = NotificationProfile
        fields = ["name", "timeslot", "filters", "active", "destinations"]
        widgets = {
            "timeslot": forms.Select(attrs={"class": "select input-bordered w-full max-w-xs"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        self.fields["timeslot"].queryset = Timeslot.objects.filter(user=user)
        self.fields["active"].widget.attrs["class"] = "checkbox checkbox-sm checkbox-accent border"
        self.fields["name"].widget.attrs["class"] = "input input-bordered"

        self.fields["filters"].queryset = Filter.objects.filter(user=user)
        self.fields["filters"].widget = DropdownMultiSelect(
            attrs={"placeholder": "select filter..."},
            partial_get="htmx:notificationprofile-filters-field",
        )
        self.fields["filters"].choices = tuple(Filter.objects.filter(user=user).values_list("id", "name"))

        self.fields["destinations"].queryset = DestinationConfig.objects.filter(user=user)
        self.fields["destinations"].widget = DropdownMultiSelect(
            attrs={"placeholder": "select destination..."},
            partial_get="htmx:notificationprofile-destinations-field",
        )
        self.fields["destinations"].choices = self._get_destination_choices(user)


class NotificationProfileFilterForm(NoColonMixin, forms.ModelForm):
    class Meta:
        model = NotificationProfile
        fields = ["filters"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["filters"].widget = DropdownMultiSelect(
            partial_get="htmx:notificationprofile-filters-field",
            attrs={"placeholder": "select filter..."},
        )
        self.fields["filters"].choices = tuple(Filter.objects.filter(user=user).values_list("id", "name"))


class NotificationProfileDestinationForm(DestinationFieldMixin, NoColonMixin, forms.ModelForm):
    class Meta:
        model = NotificationProfile
        fields = ["destinations"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["destinations"].widget = DropdownMultiSelect(
            partial_get="htmx:notificationprofile-destinations-field",
            attrs={"placeholder": "select destination..."},
        )
        self.fields["destinations"].choices = self._get_destination_choices(user)


def _render_form_field(request: HtmxHttpRequest, form, partial_template_name):
    # Not a view!
    form = form(request.GET or None, user=request.user)
    context = {"form": form}
    return render(request, partial_template_name, context=context)


def filters_form_view(request: HtmxHttpRequest):
    return _render_form_field(
        request, NotificationProfileFilterForm, "htmx/notificationprofile/_notificationprofile_form.html"
    )


def destinations_form_view(request: HtmxHttpRequest):
    return _render_form_field(
        request, NotificationProfileDestinationForm, "htmx/notificationprofile/_notificationprofile_form.html"
    )


class NotificationProfileMixin:
    "Common functionality for all views"

    model = NotificationProfile

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("timeslot")
            .prefetch_related(
                "filters",
                "destinations",
            )
        )
        return qs.filter(user_id=self.request.user.id)

    def get_template_names(self):
        if self.request.htmx and self.partial_template_name:
            return [self.partial_template_name]
        orig_app_label = self.model._meta.app_label
        orig_model_name = self.model._meta.model_name
        self.model._meta.app_label = "htmx/notificationprofile"
        self.model._meta.model_name = "notificationprofile"
        templates = super().get_template_names()
        self.model._meta.app_label = orig_app_label
        self.model._meta.model_name = orig_model_name
        return templates

    def get_success_url(self):
        return reverse("htmx:notificationprofile-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Profiles"
        return context


class ChangeMixin:
    "Common functionality for create and update views"

    form_class = NotificationProfileForm
    partial_template_name = "htmx/notificationprofile/_notificationprofile_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)


class NotificationProfileListView(NotificationProfileMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forms = []
        for obj in self.get_queryset():
            form = NotificationProfileForm(None, user=self.request.user, instance=obj)
            forms.append(form)
        context["form_list"] = forms
        return context


class NotificationProfileDetailView(NotificationProfileMixin, DetailView):
    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        return redirect("htmx:notificationprofile-update", pk=object.pk)


class NotificationProfileCreateView(ChangeMixin, NotificationProfileMixin, CreateView):
    pass


class NotificationProfileUpdateView(ChangeMixin, NotificationProfileMixin, UpdateView):
    pass


class NotificationProfileDeleteView(NotificationProfileMixin, DeleteView):
    pass
