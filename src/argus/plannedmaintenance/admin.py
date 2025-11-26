import logging

from django.contrib import admin

from .models import PlannedMaintenanceTask

LOG = logging.getLogger(__name__)


class PlannedMaintenanceTaskAdmin(admin.ModelAdmin):
    # Planned maintenance list
    list_display = (
        "owner",
        "created",
        "start_time",
        "end_time",
        "description",
    )

    list_select_related = ("owner",)
    raw_id_fields = ("owner",)
    ordering = ("start_time",)

    # Planned maintenance adding/editing
    filter_horizontal = ("filters",)
    readonly_fields = ["created"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("filters").prefetch_related("filters__user")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            LOG.debug("Planned maintenance %s changed by %s", obj.id, request.user)
        else:
            LOG.debug("Planned maintenance %s created by %s", obj.id, request.user)


admin.site.register(PlannedMaintenanceTask, PlannedMaintenanceTaskAdmin)
