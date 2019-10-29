from django.contrib import admin

from .models import NotificationProfile, Filter


class NotificationProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'interval_start', 'interval_stop')

    raw_id_fields = ('user',)


admin.site.register(NotificationProfile, NotificationProfileAdmin)
admin.site.register(Filter)

