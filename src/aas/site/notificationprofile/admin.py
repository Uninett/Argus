from django.contrib import admin
from django.db.models.functions import Concat
from django.utils.html import format_html_join

from .models import Filter, NotificationProfile, TimeInterval, TimeSlot


class TimeSlotAdmin(admin.ModelAdmin):
    class TimeIntervalInline(admin.TabularInline):
        model = TimeInterval
        # TODO: add ordering on day; probably requires representing days as numbers rather than letters
        extra = 0

    inlines = [TimeIntervalInline]

    list_display = ('name', 'user', 'get_time_intervals')
    list_filter = ('time_intervals__day',)
    search_fields = ('name', 'user__first_name', 'user__last_name', 'user__username')

    raw_id_fields = ('user',)

    def get_time_intervals(self, time_slot):
        return format_html_join(
            "", "<div>{}</div>",
            ((ts,) for ts in time_slot.time_intervals.all())
        )

    get_time_intervals.short_description = "Time intervals"


class FilterAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'filter_string')
    search_fields = (
        'name', 'filter_string',
        'user__first_name', 'user__last_name', 'user__username',
    )

    raw_id_fields = ('user',)


class NotificationProfileAdmin(admin.ModelAdmin):
    list_display = ('get_str', 'get_filters', 'get_media', 'active')
    list_filter = ('active',)
    search_fields = (
        'time_slot__name', 'filters__name', 'filters__filter_string',
        'user__first_name', 'user__last_name', 'user__username',
    )

    raw_id_fields = ('user', 'time_slot')
    filter_horizontal = ('filters',)

    def get_str(self, notification_profile):
        return f"[{notification_profile.time_slot.user}] {notification_profile.time_slot}"

    get_str.short_description = "[User] Time slot"
    get_str.admin_order_field = Concat('time_slot__user', 'time_slot__name')

    def get_filters(self, notification_profile):
        return format_html_join(
            "", "<div>{}</div>",
            ((f,) for f in notification_profile.filters.all())
        )

    get_filters.short_description = "Filters"

    def get_media(self, notification_profile):
        return notification_profile.get_media_display()

    get_media.short_description = "Notification media"
    get_media.admin_order_field = 'media'


admin.site.register(TimeSlot, TimeSlotAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(NotificationProfile, NotificationProfileAdmin)
