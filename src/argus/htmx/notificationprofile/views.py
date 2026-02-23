"""
Everything needed python-wise to CRUD notificationprofiles

See https://ccbv.co.uk/ to grok class-based views.
"""

from django import forms
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django_htmx.http import HttpResponseClientRedirect

from argus.htmx.request import HtmxHttpRequest
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
        self.fields["destinations"].widget = forms.SelectMultiple(
            attrs={"placeholder": "Select destinations..."},
        )
        self.fields["destinations"].widget.template_name = "htmx/forms/choices_select_multiple.html"
        self.fields["destinations"].choices = self._get_destination_choices(user)


class FilterFieldMixin:
    def _init_filters(self, user):
        qs = Filter.objects.usable_by(user=user)
        self.fields["filters"].queryset = qs
        self.fields["filters"].widget = forms.SelectMultiple(
            attrs={"placeholder": "Select filters..."},
        )
        self.fields["filters"].widget.template_name = "htmx/forms/choices_select_multiple.html"
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

        self.fields["filters"].help_text = "Multiple filters increase precision, not recall. They are AND-ed together."
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

    def _make_delete_modal(self, obj, **kwargs):
        return DeleteModal(
            header="Delete notification profile",
            button_title="Delete",
            button_class="btn-sm btn-outline btn-error",
            explanation=f'Delete the notification profile "{obj}"?',
            dialog_id=f"delete-modal-{obj.pk}",
            endpoint=reverse("htmx:notificationprofile-delete", kwargs={"pk": obj.pk}),
            **kwargs,
        )

    def _set_delete_modal(self, form, obj):
        form.modal = self._make_delete_modal(obj)
        return form

    def _attach_card_delete_modal(self, obj):
        obj.delete_modal = self._make_delete_modal(obj, opener_button_template_name="htmx/_blank.html")

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("timeslot")
            .prefetch_related(
                "filters",
                "destinations__media",
                "timeslot__time_recurrences",
            )
        )
        return qs.filter(user_id=self.request.user.id)

    def get_template_names(self):
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
        context["active_tab"] = "profiles"
        return context


class ChangeMixin:
    "Common functionality for create and update views"

    form_class = NotificationProfileForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        form.save_m2m()
        return self.form_valid_response()

    def form_valid_response(self):
        if self.request.htmx:
            return HttpResponseClientRedirect(self.get_success_url())
        return HttpResponseRedirect(self.get_success_url())

    def get_prefix(self):
        if self.object and self.object.pk:
            prefix = f"npf{self.object.pk}"
            return prefix
        return self.prefix


class NotificationProfileListView(NotificationProfileMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for obj in context["object_list"]:
            self._attach_card_delete_modal(obj)
        return context


class NotificationProfileDetailView(NotificationProfileMixin, DetailView):
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.htmx:
            self._attach_card_delete_modal(obj)
            return TemplateResponse(
                request,
                "htmx/notificationprofile/_notificationprofile_card.html",
                {"profile": obj},
            )
        return redirect("htmx:notificationprofile-update", pk=obj.pk)


class NotificationProfileCreateView(ChangeMixin, NotificationProfileMixin, CreateView):
    def get_template_names(self):
        if self.request.htmx:
            return ["htmx/notificationprofile/_notificationprofile_form.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context


class NotificationProfileUpdateView(ChangeMixin, NotificationProfileMixin, UpdateView):
    def get_template_names(self):
        if self.request.htmx:
            return ["htmx/notificationprofile/_notificationprofile_form_content.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        context["form"] = self._set_delete_modal(form, self.object)
        return context

    def form_valid_response(self):
        if self.request.htmx:
            context = self.get_context_data()
            context["profile"] = self.object
            now = timezone.localtime().strftime("%H:%M:%S")
            context["success_message"] = f'Saved profile "{self.object}" at {now}.'
            return self.render_to_response(context)
        return HttpResponseRedirect(self.get_success_url())


class NotificationProfileDeleteView(NotificationProfileMixin, DeleteView):
    pass
