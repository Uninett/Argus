from django.contrib import admin

from .models import Alert, AlertRelation, AlertRelationType, NetworkSystem, NetworkSystemType, Object, ObjectType, ParentObject, ProblemType


class NetworkSystemTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class NetworkSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')


class ObjectTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ObjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'object_id', 'type', 'network_system')


class ParentObjectAdmin(admin.ModelAdmin):
    list_display = ('get_str', 'name', 'url')

    def get_str(self, parent_object):
        return str(parent_object)

    get_str.short_description = "Parent object"
    get_str.admin_order_field = 'parentobject_id'


class ProblemTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_id', 'timestamp', 'source', 'object', 'parent_object', 'details_url', 'problem_type', 'ticket_url')
    search_fields = (
        'alert_id',
        'source__name', 'source__type__name',
        'object__name', 'object__object_id', 'object__type__name',
        'parent_object__name', 'parent_object__parentobject_id',
        'problem_type__name',
    )
    list_filter = ('problem_type', 'source', 'source__type')

    raw_id_fields = ('object', 'parent_object')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Reduce number of database calls
        return qs.prefetch_related('source', 'object', 'parent_object', 'problem_type')


class AlertRelationTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class AlertRelationAdmin(admin.ModelAdmin):
    list_display = ('get_str', 'type', 'description')
    search_fields = ('alert1__alert_id', 'alert2__alert_id')

    raw_id_fields = ('alert1', 'alert2')

    def get_str(self, alert_relation):
        return str(alert_relation)

    get_str.short_description = "Alert relation"


admin.site.register(NetworkSystemType, NetworkSystemTypeAdmin)
admin.site.register(NetworkSystem, NetworkSystemAdmin)
admin.site.register(ObjectType, ObjectTypeAdmin)
admin.site.register(Object, ObjectAdmin)
admin.site.register(ParentObject, ParentObjectAdmin)
admin.site.register(ProblemType, ProblemTypeAdmin)
admin.site.register(Alert, AlertAdmin)

admin.site.register(AlertRelation, AlertRelationAdmin)
admin.site.register(AlertRelationType, AlertRelationTypeAdmin)
