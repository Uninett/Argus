from django.contrib import admin
from django.db.models.functions import Concat
from django.utils.html import format_html_join

from .models import DestinationConfig, Filter, Media, NotificationProfile, TimeRecurrence, Timeslot


@admin.action(description="Toggle activation for selected profiles")
def toggle_activation(modeladmin, request, queryset):
    for profile in queryset:
        profile.active = not profile.active
        profile.save()


@admin.action(description="Activate selected profiles")
def activate_profiles(modeladmin, request, queryset):
    queryset.update(active=True)


@admin.action(description="Deactivate selected profiles")
def deactivate_profiles(modeladmin, request, queryset):
    queryset.update(active=False)


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

    def get_time_recurrences(self, timeslot: Timeslot):
        return format_html_join("", "<div>{}</div>", ((ts,) for ts in timeslot.time_recurrences.all()))

    get_time_recurrences.short_description = "Time recurrences"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Reduce number of database calls
        return qs.select_related("user").prefetch_related("time_recurrences")


class FilterAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "filter")
    search_fields = (
        "name",
        "filter",
        "user__first_name",
        "user__last_name",
        "user__username",
    )
    list_select_related = ("user",)

    raw_id_fields = ("user",)


class MediaAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "name",
    )
    fields = ("name",)


class DestinationConfigAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "media",
        "label",
        "settings",
    )
    list_filter = ("media__name",)
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__username",
        "label",
    )
    raw_id_fields = ("user",)
    ordering = ("user",)


class DestinationConfigInline(admin.TabularInline):
    model = NotificationProfile.destinations.through


class NotificationProfileAdmin(admin.ModelAdmin):
    list_display = ("get_str", "user", "get_filters", "get_destination_media", "active")
    list_filter = (
        "active",
        "user",
    )
    search_fields = (
        "name",
        "timeslot__name",
        "filters__name",
        "filters__filter",
        "user__first_name",
        "user__last_name",
        "user__username",
    )
    ordering = ("user",)
    actions = [toggle_activation, activate_profiles, deactivate_profiles]

    raw_id_fields = ("user", "timeslot")
    filter_horizontal = ("filters",)

    inlines = [
        DestinationConfigInline,
    ]
    exclude = ("destinations",)

    def get_str(self, notification_profile: NotificationProfile):
        if notification_profile.name:
            return f"{notification_profile.name}"
        return f"[{notification_profile.timeslot.user}] {notification_profile.timeslot}"

    get_str.short_description = "Name"
    get_str.admin_order_field = Concat("name", "timeslot__user", "timeslot__name")

    def get_filters(self, notification_profile: NotificationProfile):
        return format_html_join("", "<div>{}</div>", ((f,) for f in notification_profile.filters.all()))

    get_filters.short_description = "Filters"

    def get_destination_media(self, notification_profile: NotificationProfile):
        return f'{" ".join(str(x) for x in set([destination.media.name for destination in notification_profile.destinations.all()]))}'

    get_destination_media.short_description = "Media"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Reduce number of database calls
        return qs.prefetch_related("timeslot__user", "filters")

    def get_form(self, request, obj=None, **kwargs):
        self.instance = obj
        return super(NotificationProfileAdmin, self).get_form(request, obj=obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "filters" and self.instance:
            kwargs["queryset"] = Filter.objects.filter(user=NotificationProfile.objects.get(pk=self.instance.pk).user)
        return super(NotificationProfileAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(Timeslot, TimeslotAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(Media, MediaAdmin)
admin.site.register(DestinationConfig, DestinationConfigAdmin)
admin.site.register(NotificationProfile, NotificationProfileAdmin)
