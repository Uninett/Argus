import logging

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils import timezone

from argus.util.admin_utils import list_filter_factory

from .models import PlannedMaintenanceTask

LOG = logging.getLogger(__name__)


@admin.action(description="End selected planned maintenance tasks now")
def end_pms(modeladmin, request, queryset):
    for pm in queryset:
        pm.end_time = timezone.now()
        pm.save()


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
    )
    list_filter = [
        ("owner", admin.RelatedOnlyFieldListFilter),
        list_filter_factory(
            "open",
            lambda qs, yes_filter: qs.filter(end_time__gt=timezone.now())
            if yes_filter
            else qs.filter(end_time__lte=timezone.now()),
        ),
    ]

    list_select_related = ("owner",)
    raw_id_fields = ("owner",)
    ordering = ("start_time",)

    actions = [end_pms]

    # Planned maintenance adding/editing
    filter_horizontal = ("filters",)
    readonly_fields = ["created"]

    change_form_template = "plannedmaintenance/admin/planned_maintenance_change_form.html"

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
        pm.end_time = timezone.now()
        pm.save()
        return HttpResponseRedirect("../../")


admin.site.register(PlannedMaintenanceTask, PlannedMaintenanceTaskAdmin)
