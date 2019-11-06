from django.contrib import admin


from .models import NotificationProfile,TimeSlot, TimeSlotGroup, Filter



class NotificationProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'media')

    raw_id_fields = ('user',)


admin.site.register(TimeSlotGroup)
admin.site.register(TimeSlot)
admin.site.register(Filter)
admin.site.register(NotificationProfile, NotificationProfileAdmin)
