from django.contrib import admin
from django.contrib.admin import widgets
from django.db.models.functions import Concat
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

from .forms import AddSourceSystemForm
from .models import (
    Incident,
    IncidentQuerySet,
    IncidentRelation,
    IncidentRelationType,
    IncidentTagRelation,
    SourceSystem,
    SourceSystemType,
    Tag,
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


class TagAdmin(TextWidgetsOverrideModelAdmin):
    list_display = ("get_str",)
    search_fields = ("key", "value")
    ordering = [Concat("key", "value")]

    text_input_form_fields = ("key", "value")

    def get_str(self, tag: Tag):
        return str(tag)

    get_str.short_description = "Tag"
    get_str.admin_order_field = Concat("key", "value")


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
    class IncidentTagRelationInline(admin.TabularInline):
        model = IncidentTagRelation
        ordering = ["tag__key", "tag__value"]
        readonly_fields = ("added_time",)
        raw_id_fields = ("tag", "added_by")
        min_num = 1
        extra = 0

    inlines = [IncidentTagRelationInline]

    list_display = (
        "source_incident_id",
        "start_time",
        "end_time",
        "source",
        "get_tags",
        "description",
        "details_url",
        "ticket_url",
    )
    search_fields = (
        "description",
        "source_incident_id",
        "source__name",
        "source__type__name",
        "incident_tag_relations__tag__key",
        "incident_tag_relations__tag__value",
    )
    list_filter = (
        StatefulListFilter,
        ActiveListFilter,
        "source",
        "source__type",
    )

    text_input_form_fields = ("source_incident_id",)
    url_input_form_fields = ("details_url", "ticket_url")

    def get_tags(self, incident: Incident):
        html_open_tag = '<div style="display: inline-block; white-space: nowrap;">'
        html_bullet = "<b>&bull;</b>"
        return format_html_join(
            mark_safe("<br />"), f"{html_open_tag}{html_bullet} {{}}</div>", ((tag,) for tag in incident.tags)
        )

    get_tags.short_description = "Tags"

    def get_queryset(self, request):
        qs: IncidentQuerySet = super().get_queryset(request)
        # Reduce number of database calls
        return qs.prefetch_default_related()


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

    def get_str(self, incident_relation: IncidentRelation):
        return str(incident_relation)

    get_str.short_description = "Incident relation"


admin.site.register(SourceSystemType, SourceSystemTypeAdmin)
admin.site.register(SourceSystem, SourceSystemAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Incident, IncidentAdmin)

admin.site.register(IncidentRelation, IncidentRelationAdmin)
admin.site.register(IncidentRelationType, IncidentRelationTypeAdmin)
