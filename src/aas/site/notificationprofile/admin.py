from django.contrib import admin

from .models import NotificationProfile


class NotificationProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'time_slot_group', 'media')

    raw_id_fields = ('user',)


admin.site.register(NotificationProfile, NotificationProfileAdmin)
