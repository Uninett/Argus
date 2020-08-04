from django.contrib import admin
from django.contrib.admin import widgets

from .forms import AddSourceSystemForm
from .models import (
    Incident,
    IncidentQuerySet,
    IncidentRelation,
    IncidentRelationType,
    Object,
    ObjectType,
    ParentObject,
    ProblemType,
    SourceSystem,
    SourceSystemType,
)


class TextWidgetsOverrideModelAdmin(admin.ModelAdmin):
    text_input_form_fields = ()
    url_input_form_fields = ()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        for form_field in self.text_input_form_fields:
            form.base_fields[form_field].widget = widgets.AdminTextInputWidget()
        for form_field in self.url_input_form_fields:
            form.base_fields[form_field].widget = widgets.AdminURLFieldWidget()

        return form


class SourceSystemTypeAdmin(TextWidgetsOverrideModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    text_input_form_fields = ("name",)


class SourceSystemAdmin(TextWidgetsOverrideModelAdmin):
    list_display = ("name", "type", "user")
    search_fields = ("name", "user__username")
    list_filter = ("type",)

    text_input_form_fields = ("name",)
    raw_id_fields = ("user",)

    def get_form(self, request, obj=None, **kwargs):
        # If add form (instead of change form):
        if not obj:
            kwargs["form"] = AddSourceSystemForm

        return super().get_form(request, obj, **kwargs)


class ObjectTypeAdmin(TextWidgetsOverrideModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    text_input_form_fields = ("name",)


class ObjectAdmin(TextWidgetsOverrideModelAdmin):
    list_display = ("name", "object_id", "type", "source_system")
    search_fields = ("name", "object_id", "type__name", "url")
    list_filter = ("source_system", "source_system__type", "type")
    list_select_related = ("type", "source_system")

    text_input_form_fields = ("name", "object_id")
    url_input_form_fields = ("url",)


class ParentObjectAdmin(TextWidgetsOverrideModelAdmin):
    list_display = ("get_str", "name", "url")
    search_fields = ("name", "parentobject_id", "url")

    text_input_form_fields = ("name", "parentobject_id")
    url_input_form_fields = ("url",)

    def get_str(self, parent_object):
        return str(parent_object)

    get_str.short_description = "Parent object"
    get_str.admin_order_field = "parentobject_id"


class ProblemTypeAdmin(TextWidgetsOverrideModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")

    text_input_form_fields = ("name",)


class StatefulListFilter(admin.SimpleListFilter):
    title = "stateful"
    # Parameter for the filter that will be used in the URL query
    parameter_name = "stateful"

    STATEFUL = 1
    STATELESS = 0

    def lookups(self, request, model_admin):
        return (
            (self.STATEFUL, "Yes"),
            (self.STATELESS, "No"),
        )

    def queryset(self, request, queryset: IncidentQuerySet):
        if not self.value():
            return queryset

        if int(self.value()) == self.STATEFUL:
            return queryset.stateful()
        else:
            return queryset.stateless()


class ActiveListFilter(admin.SimpleListFilter):
    title = "active"
    # Parameter for the filter that will be used in the URL query
    parameter_name = "active"

    ACTIVE = 1
    INACTIVE = 0

    def lookups(self, request, model_admin):
        return (
            (self.ACTIVE, "Yes"),
            (self.INACTIVE, "No"),
        )

    def queryset(self, request, queryset: IncidentQuerySet):
        if not self.value():
            return queryset

        if int(self.value()) == self.ACTIVE:
            return queryset.active()
        else:
            return queryset.inactive()


class IncidentAdmin(TextWidgetsOverrideModelAdmin):
    list_display = (
        "source_incident_id",
        "start_time",
        "end_time",
        "source",
        "object",
        "parent_object",
        "details_url",
        "problem_type",
        "ticket_url",
    )
    search_fields = (
        "source_incident_id",
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
        StatefulListFilter,
        ActiveListFilter,
        "source",
        "source__type",
        "problem_type",
        "object__type",
    )

    raw_id_fields = ("object", "parent_object")
    text_input_form_fields = ("source_incident_id",)
    url_input_form_fields = ("details_url", "ticket_url")

    def get_queryset(self, request):
        qs: IncidentQuerySet = super().get_queryset(request)
        # Reduce number of database calls
        return qs.prefetch_default_related().prefetch_related("object__source_system__type")


class IncidentRelationTypeAdmin(TextWidgetsOverrideModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

    text_input_form_fields = ("name",)


class IncidentRelationAdmin(admin.ModelAdmin):
    list_display = ("get_str", "type", "description")
    search_fields = ("incident1__source_incident_id", "incident2__source_incident_id")
    list_filter = ("type",)
    list_select_related = ("type",)

    raw_id_fields = ("incident1", "incident2")

    def get_str(self, incident_relation):
        return str(incident_relation)

    get_str.short_description = "Incident relation"


admin.site.register(SourceSystemType, SourceSystemTypeAdmin)
admin.site.register(SourceSystem, SourceSystemAdmin)
admin.site.register(ObjectType, ObjectTypeAdmin)
admin.site.register(Object, ObjectAdmin)
admin.site.register(ParentObject, ParentObjectAdmin)
admin.site.register(ProblemType, ProblemTypeAdmin)
admin.site.register(Incident, IncidentAdmin)

admin.site.register(IncidentRelation, IncidentRelationAdmin)
admin.site.register(IncidentRelationType, IncidentRelationTypeAdmin)
