from django.contrib import admin
from django.db.models.functions import Concat
from django.utils.html import format_html_join

from argus.util.admin_utils import list_filter_factory
from ..admin import FilterAdmin, TimeslotAdmin
from ..models import Filter, NotificationProfile, Timeslot


class NotificationProfileAdminV1(admin.ModelAdmin):
    list_display = ("get_str", "get_filters", "get_media", "active")
    list_filter = (
        "active",
        list_filter_factory("has phone number", lambda qs, yes_filter: qs.exclude(phone_number__isnull=yes_filter)),
    )
    search_fields = (
        "timeslot__name",
        "filters__name",
        "filters__filter_string",
        "user__first_name",
        "user__last_name",
        "user__username",
    )

    raw_id_fields = ("user", "timeslot")
    filter_horizontal = ("filters",)

    def get_str(self, notification_profile: NotificationProfile):
        return f"[{notification_profile.timeslot.user}] {notification_profile.timeslot}"

    get_str.short_description = "[User] Time slot"
    get_str.admin_order_field = Concat("timeslot__user", "timeslot__name")

    def get_filters(self, notification_profile: NotificationProfile):
        return format_html_join("", "<div>{}</div>", ((f,) for f in notification_profile.filters.all()))

    get_filters.short_description = "Filters"

    def get_media(self, notification_profile: NotificationProfile):
        return notification_profile.get_media_v1_display()

    get_media.short_description = "Notification media"
    get_media.admin_order_field = "media_v1"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Reduce number of database calls
        return qs.prefetch_related("timeslot__user", "filters")


admin.site.register(Timeslot, TimeslotAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(NotificationProfile, NotificationProfileAdminV1)
