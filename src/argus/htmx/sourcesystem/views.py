from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, ProtectedError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from rest_framework.authtoken.models import Token

from argus.htmx.plannedmaintenance.views import UserIsStaffMixin
from argus.htmx.utils import TemplateNameViewMixin
from argus.incident.models import SourceSystem, SourceSystemType

from .forms import AddSourceSystemTypeForm, CreateSourceSystemForm, UpdateSourceSystemForm


class SourceSystemMixin(TemplateNameViewMixin):
    model = SourceSystem
    template_name_piece = "sourcesystem"

    def get_success_url(self):
        return reverse("htmx:sourcesystem-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sources"
        context["active_tab"] = "sources"
        return context


class SourceSystemTypeMixin(TemplateNameViewMixin):
    model = SourceSystemType
    template_name_piece = "sourcesystem"

    def get_success_url(self):
        return reverse("htmx:sourcesystemtype-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sources"
        context["active_tab"] = "types"
        return context


class SourceSystemListView(SourceSystemMixin, ListView):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("type", "user", "user__auth_token")
            .annotate(incident_count=Count("incidents"))
            .order_by("name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expiration_duration = timedelta(days=settings.AUTH_TOKEN_EXPIRES_AFTER_DAYS)
        now = timezone.now()
        for source in context["object_list"]:
            token = getattr(source.user, "auth_token", None)
            if token is None:
                source.token_status = "missing"
            elif token.created + expiration_duration < now:
                source.token_status = "expired"
            else:
                source.token_status = "valid"
        return context


class SourceSystemCreateView(UserIsStaffMixin, SourceSystemMixin, CreateView):
    form_class = CreateSourceSystemForm


class SourceSystemUpdateView(UserIsStaffMixin, SourceSystemMixin, UpdateView):
    form_class = UpdateSourceSystemForm


class ProtectedDeleteMixin:
    protected_error_message = 'Cannot delete "{object}".'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(request, self.protected_error_message.format(object=self.object))
        return HttpResponseRedirect(self.get_success_url())


class SourceSystemDeleteView(UserIsStaffMixin, SourceSystemMixin, ProtectedDeleteMixin, DeleteView):
    protected_error_message = 'Cannot delete source "{object}" because it has associated incidents.'


class SourceSystemTokenView(UserIsStaffMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        source = get_object_or_404(SourceSystem, pk=pk)
        Token.objects.filter(user=source.user).delete()
        token = Token.objects.create(user=source.user)
        messages.success(
            request,
            f'New token for "{source}": {token.key}',
        )
        return HttpResponseRedirect(reverse("htmx:sourcesystem-list"))


class SourceSystemTypeListView(SourceSystemTypeMixin, ListView):
    def get_queryset(self):
        return SourceSystemType.objects.annotate(source_count=Count("instances")).order_by("name")

    def get_template_names(self):
        return ["htmx/sourcesystem/sourcesystemtype_list.html"]


class SourceSystemTypeCreateView(UserIsStaffMixin, SourceSystemTypeMixin, CreateView):
    form_class = AddSourceSystemTypeForm

    def get_template_names(self):
        return ["htmx/sourcesystem/sourcesystemtype_form.html"]


class SourceSystemTypeDeleteView(UserIsStaffMixin, SourceSystemTypeMixin, ProtectedDeleteMixin, DeleteView):
    protected_error_message = 'Cannot delete type "{object}" because it has associated source systems.'
