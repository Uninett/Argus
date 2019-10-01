from django.contrib import admin

from .models import AlertHistory, AlertQueue, AlertType, EventType, NetworkSystem, NetworkSystemType, Subject, SubjectType


class NetworkSystemTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class NetworkSystemAdmin(admin.ModelAdmin):
    list_display = ('name', 'type')


class SubjectTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject_id', 'type')


class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


class AlertTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


class AlertBaseAdmin(admin.ModelAdmin):
    list_display = ('type', 'event_type', 'subject', 'network_system')

    raw_id_fields = ('subject',)


class AlertQueueAdmin(AlertBaseAdmin):
    list_display = ('alert_id', 'timestamp') + AlertBaseAdmin.list_display


class AlertHistoryAdmin(AlertBaseAdmin):
    list_display = ('alert_id', 'start_time', 'end_time') + AlertBaseAdmin.list_display


admin.site.register(NetworkSystemType, NetworkSystemTypeAdmin)
admin.site.register(NetworkSystem, NetworkSystemAdmin)
admin.site.register(SubjectType, SubjectTypeAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(EventType, EventTypeAdmin)
admin.site.register(AlertType, AlertTypeAdmin)
admin.site.register(AlertQueue, AlertQueueAdmin)
admin.site.register(AlertHistory, AlertHistoryAdmin)
