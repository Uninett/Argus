from django.contrib import admin

from .models import NotificationProfile,TimeSlot, TimeSlotGroup



class NotificationProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'media')

    raw_id_fields = ('user',)


admin.site.register(NotificationProfile, NotificationProfileAdmin)

admin.site.register(TimeSlot)

admin.site.register(TimeSlotGroup)

