from django.contrib import admin
from django.db.models.functions import Concat
from django.utils.html import format_html_join

from .models import Filter, NotificationProfile, TimeRecurrence, Timeslot


class TimeslotAdmin(admin.ModelAdmin):
    class TimeRecurrenceInline(admin.TabularInline):
        model = TimeRecurrence
        ordering = ["days"]
        min_num = 1
        extra = 0

    inlines = [TimeRecurrenceInline]

    list_display = ("name", "user", "get_time_recurrences")
    search_fields = ("name", "user__first_name", "user__last_name", "user__username")

    raw_id_fields = ("user",)

    def get_time_recurrences(self, timeslot):
        return format_html_join("", "<div>{}</div>", ((ts,) for ts in timeslot.time_recurrences.all()))

    get_time_recurrences.short_description = "Time recurrences"


class FilterAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "filter_string")
    search_fields = (
        "name",
        "filter_string",
        "user__first_name",
        "user__last_name",
        "user__username",
    )

    raw_id_fields = ("user",)


class HasPhoneNumberFilter(admin.SimpleListFilter):
    title = "has phone number"
    parameter_name = "has_phone_number"
    YES = 1
    NO = 0

    def lookups(self, request, model_admin):
        return ((self.YES, "Yes"), (self.NO, "No"))

    def queryset(self, request, queryset):
        try:
            value = bool(int(self.value()))
        except ValueError:
            return queryset
        return queryset.exclude(phone_number__isnull=value)


class NotificationProfileAdmin(admin.ModelAdmin):
    list_display = ("get_str", "get_filters", "get_media", "active")
    list_filter = ("active", HasPhoneNumberFilter)
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

    def get_str(self, notification_profile):
        return f"[{notification_profile.timeslot.user}] {notification_profile.timeslot}"

    get_str.short_description = "[User] Time slot"
    get_str.admin_order_field = Concat("timeslot__user", "timeslot__name")

    def get_filters(self, notification_profile):
        return format_html_join("", "<div>{}</div>", ((f,) for f in notification_profile.filters.all()))

    get_filters.short_description = "Filters"

    def get_media(self, notification_profile):
        return notification_profile.get_media_display()

    get_media.short_description = "Notification media"
    get_media.admin_order_field = "media"


admin.site.register(Timeslot, TimeslotAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(NotificationProfile, NotificationProfileAdmin)
