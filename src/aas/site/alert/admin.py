from django.contrib import admin

from .models import Alert, NetworkSystem, NetworkSystemType, Object, ObjectType, ParentObject, ProblemType


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
    list_display = ('alert_id', 'timestamp', 'source', 'object', 'parent_object', 'details_url', 'problem_type')

    raw_id_fields = ('object', 'parent_object')


admin.site.register(NetworkSystemType, NetworkSystemTypeAdmin)
admin.site.register(NetworkSystem, NetworkSystemAdmin)
admin.site.register(ObjectType, ObjectTypeAdmin)
admin.site.register(Object, ObjectAdmin)
admin.site.register(ParentObject, ParentObjectAdmin)
admin.site.register(ProblemType, ProblemTypeAdmin)
admin.site.register(Alert, AlertAdmin)
