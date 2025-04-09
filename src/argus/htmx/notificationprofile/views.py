"""
Everything needed python-wise to CRUD notificationprofiles

See https://ccbv.co.uk/ to grok class-based views.
"""

from django import forms
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from argus.htmx.request import HtmxHttpRequest
from argus.htmx.widgets import DropdownMultiSelect
from argus.notificationprofile.media import MEDIA_CLASSES_DICT
from argus.htmx.modals import DeleteModal
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

    def _init_destinations(self, user):
        qs = DestinationConfig.objects.filter(user=user)
        self.fields["destinations"].queryset = qs
        if self.instance.id:
            partial_get = reverse(
                "htmx:notificationprofile-destinations-field-update",
                kwargs={"pk": self.instance.pk},
            )
        else:
            partial_get = reverse("htmx:notificationprofile-destinations-field-create")
        self.fields["destinations"].widget = DropdownMultiSelect(
            partial_get=partial_get,
            attrs={
                "placeholder": "select destination...",
                "field_styles": "input input-bordered border-b max-w-xs",
            },
        )
        self.fields["destinations"].choices = self._get_destination_choices(user)


class FilterFieldMixin:
    def _init_filters(self, user):
        qs = Filter.objects.filter(user=user)
        self.fields["filters"].queryset = qs

        if self.instance.id:
            partial_get = reverse(
                "htmx:notificationprofile-filters-field-update",
                kwargs={"pk": self.instance.pk},
            )
        else:
            partial_get = reverse("htmx:notificationprofile-filters-field-create")
        self.fields["filters"].widget = DropdownMultiSelect(
            partial_get=partial_get,
            attrs={
                "placeholder": "select filter...",
                "field_styles": "input input-bordered border-b max-w-xs",
            },
        )
        self.fields["filters"].choices = tuple(qs.values_list("id", "name"))


class NotificationProfileForm(DestinationFieldMixin, FilterFieldMixin, NoColonMixin, forms.ModelForm):
    class Meta:
        model = NotificationProfile
        fields = ["name", "timeslot", "filters", "active", "destinations"]
        widgets = {
            "timeslot": forms.Select(attrs={"class": "select input-bordered w-full max-w-xs"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

        self.template_name_div = "htmx/notificationprofile/_notificationprofile_form_div.html"

        self.fields["timeslot"].queryset = Timeslot.objects.filter(user=self.user)
        self.fields["active"].widget.attrs["class"] = "checkbox checkbox-sm border"
        self.fields["active"].widget.attrs["autocomplete"] = "off"
        self.fields["name"].widget.attrs["class"] = "input input-bordered"

        self.action = self.get_action()

        self._init_filters(self.user)
        self._init_destinations(self.user)

    def get_action(self):
        if self.instance and self.instance.pk:
            return reverse("htmx:notificationprofile-update", kwargs={"pk": self.instance.pk})
        else:
            return reverse("htmx:notificationprofile-create")

    def clean_name(self):
        name = self.cleaned_data["name"]
        # Making sure to check for duplicate names, but allow updating of profiles
        profiles_with_same_name = NotificationProfile.objects.filter(user=self.user, name=name).exclude(
            pk=getattr(self.instance, "pk", None)
        )
        if profiles_with_same_name.exists():
            raise forms.ValidationError(f"A profile by this user with the name '{name}' already exists.")
        return name


class NotificationProfileFilterForm(FilterFieldMixin, NoColonMixin, forms.ModelForm):
    class Meta:
        model = NotificationProfile
        fields = ["filters"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self._init_filters(user)


class NotificationProfileDestinationForm(DestinationFieldMixin, NoColonMixin, forms.ModelForm):
    class Meta:
        model = NotificationProfile
        fields = ["destinations"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self._init_destinations(user)


def _render_form_field(request: HtmxHttpRequest, form, partial_template_name, prefix=None):
    # Not a view!
    form = form(request.GET or None, user=request.user, prefix=prefix)
    context = {"form": form}
    return render(request, partial_template_name, context=context)


@require_GET
def filters_form_view(request: HtmxHttpRequest, pk: int = None):
    prefix = f"npf{pk}" if pk else None
    return _render_form_field(
        request,
        NotificationProfileFilterForm,
        "htmx/notificationprofile/_notificationprofile_form.html",
        prefix=prefix,
    )


@require_GET
def destinations_form_view(request: HtmxHttpRequest, pk: int = None):
    prefix = f"npf{pk}" if pk else None
    return _render_form_field(
        request,
        NotificationProfileDestinationForm,
        "htmx/notificationprofile/_notificationprofile_form.html",
        prefix=prefix,
    )


class NotificationProfileMixin:
    "Common functionality for all views"

    model = NotificationProfile

    def _set_delete_modal(self, form, obj):
        form.modal = DeleteModal(
            header="Delete notification profile",
            explanation=f'Delete the notification profile "{obj}"?',
            dialog_id=f"delete-modal-{obj.pk}",
            endpoint=reverse("htmx:notificationprofile-delete", kwargs={"pk": obj.pk}),
        )
        return form

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
        if self.request.htmx and hasattr(self, "partial_template_name"):
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
        return super().form_valid(form)

    def get_prefix(self):
        if self.object and self.object.pk:
            prefix = f"npf{self.object.pk}"
            return prefix
        return self.prefix


class NotificationProfileListView(NotificationProfileMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forms = []
        for obj in self.get_queryset():
            form = NotificationProfileForm(None, prefix=f"npf{obj.pk}", user=self.request.user, instance=obj)
            form = self._set_delete_modal(form, obj)
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
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        context["form"] = self._set_delete_modal(form, self.object)
        return context


class NotificationProfileDeleteView(NotificationProfileMixin, DeleteView):
    pass
