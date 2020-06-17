from django.contrib import admin

from .models import (
    ActiveAlert,
    Alert,
    AlertRelation,
    AlertRelationType,
    AlertSource,
    Object,
    ObjectType,
    ParentObject,
    ProblemType,
)


class AlertSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    search_fields = ("name",)
    list_filter = ("type",)


class ObjectTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class ObjectAdmin(admin.ModelAdmin):
    list_display = ("name", "object_id", "type", "alert_source")
    search_fields = ("name", "object_id", "type__name", "url")
    list_filter = ("alert_source", "alert_source__type", "type")
    list_select_related = ("type", "alert_source")


class ParentObjectAdmin(admin.ModelAdmin):
    list_display = ("get_str", "name", "url")
    search_fields = ("name", "parentobject_id", "url")

    def get_str(self, parent_object):
        return str(parent_object)

    get_str.short_description = "Parent object"
    get_str.admin_order_field = "parentobject_id"


class ProblemTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


class ActiveStateListFilter(admin.SimpleListFilter):
    title = "active state"
    # Parameter for the filter that will be used in the URL query
    parameter_name = "active"

    def lookups(self, request, model_admin):
        return (
            (1, "Yes"),
            (0, "No"),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        lookup_value = int(self.value())
        return queryset.filter(active_state__isnull=not lookup_value)


class AlertAdmin(admin.ModelAdmin):
    list_display = (
        "alert_id",
        "timestamp",
        "source",
        "object",
        "parent_object",
        "details_url",
        "problem_type",
        "ticket_url",
        "get_active_state",
    )
    search_fields = (
        "alert_id",
        "source__name",
        "source__type",
        "object__name",
        "object__object_id",
        "object__type__name",
        "parent_object__name",
        "parent_object__parentobject_id",
        "problem_type__name",
    )
    list_filter = (
        ActiveStateListFilter,
        "source",
        "source__type",
        "problem_type",
        "object__type",
    )
    list_select_related = ("active_state",)

    raw_id_fields = ("object", "parent_object")

    def get_active_state(self, alert: Alert):
        return hasattr(alert, "active_state")

    get_active_state.boolean = True
    get_active_state.short_description = "Active"
    get_active_state.admin_order_field = "active_state"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Reduce number of database calls
        return Alert.prefetch_related_fields(qs)


class ActiveAlertAdmin(admin.ModelAdmin):
    list_display = ("alert",)
    search_fields = ("alert__alert_id",)
    list_select_related = ("alert",)

    raw_id_fields = ("alert",)


class AlertRelationTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class AlertRelationAdmin(admin.ModelAdmin):
    list_display = ("get_str", "type", "description")
    search_fields = ("alert1__alert_id", "alert2__alert_id")
    list_filter = ("type",)
    list_select_related = ("type",)

    raw_id_fields = ("alert1", "alert2")

    def get_str(self, alert_relation):
        return str(alert_relation)

    get_str.short_description = "Alert relation"


admin.site.register(AlertSource, AlertSourceAdmin)
admin.site.register(ObjectType, ObjectTypeAdmin)
admin.site.register(Object, ObjectAdmin)
admin.site.register(ParentObject, ParentObjectAdmin)
admin.site.register(ProblemType, ProblemTypeAdmin)
admin.site.register(Alert, AlertAdmin)
admin.site.register(ActiveAlert, ActiveAlertAdmin)

admin.site.register(AlertRelation, AlertRelationAdmin)
admin.site.register(AlertRelationType, AlertRelationTypeAdmin)
