import logging

from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils import timezone

from argus.util.admin_utils import list_filter_factory

from .models import PlannedMaintenanceTask

LOG = logging.getLogger(__name__)


@admin.action(description="Mark selected planned maintenance tasks as finished")
def cancel_pms(modeladmin, request, queryset):
    now = timezone.now()
    queryset = queryset.filter(end_time__gt=now)
    for pm in queryset:
        pm.cancel(end_time=now)


class PlannedMaintenanceTaskAdmin(admin.ModelAdmin):
    # Planned maintenance list
    list_display = (
        "owner",
        "created",
        "start_time",
        "end_time",
        "description",
    )
    search_fields = (
        "description",
        "owner__first_name",
        "owner__last_name",
        "owner__username",
        "filters__name",
        "filters__user__first_name",
        "filters__user__last_name",
        "filters__user__username",
    )
    list_filter = [
        ("owner", admin.RelatedOnlyFieldListFilter),
        list_filter_factory(
            "future",
            lambda qs, yes_filter: qs.future() if yes_filter else qs.filter(start_time__lte=timezone.now()),
        ),
        list_filter_factory(
            "past",
            lambda qs, yes_filter: qs.past() if yes_filter else qs.filter(end_time__gte=timezone.now()),
        ),
        list_filter_factory(
            "current",
            lambda qs, yes_filter: qs.current()
            if yes_filter
            else qs.filter(Q(start_time__gt=timezone.now()) | Q(end_time__lt=timezone.now())),
        ),
    ]

    list_select_related = ("owner",)
    raw_id_fields = ("owner",)
    ordering = ("start_time",)

    actions = [cancel_pms]

    # Planned maintenance adding/editing
    filter_horizontal = ("filters",)
    readonly_fields = ["created"]

    change_form_template = "plannedmaintenance/admin/planned_maintenance_change_form.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("filters").prefetch_related("filters__user")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            LOG.debug("Planned maintenance %s changed by %s", obj.id, request.user)
        else:
            LOG.debug("Planned maintenance %s created by %s", obj.id, request.user)

    def get_urls(self):
        orig_urls = super().get_urls()
        urls = [
            path(
                "<int:pk>/cancel/",
                self.admin_site.admin_view(self.cancel_planned_maintenance_task),
                name="cancel-pm-task",
            )
        ]
        return urls + orig_urls

    def cancel_planned_maintenance_task(self, request, pk: int):
        pm = PlannedMaintenanceTask.objects.get(id=pk)
        pm.cancel()

        return HttpResponseRedirect(reverse("admin:argus_plannedmaintenance_plannedmaintenancetask_changelist"))


admin.site.register(PlannedMaintenanceTask, PlannedMaintenanceTaskAdmin)
