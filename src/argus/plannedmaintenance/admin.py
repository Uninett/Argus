import logging

from django.contrib import admin
from django.utils import timezone

from argus.util.admin_utils import list_filter_factory

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

    # Planned maintenance adding/editing
    filter_horizontal = ("filters",)
    readonly_fields = ["created"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change:
            LOG.debug("Planned maintenance %s changed by %s", obj.id, request.user)
        else:
            LOG.debug("Planned maintenance %s created by %s", obj.id, request.user)


admin.site.register(PlannedMaintenanceTask, PlannedMaintenanceTaskAdmin)
