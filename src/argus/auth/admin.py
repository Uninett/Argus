from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User
from argus.notificationprofile.models import DestinationConfig


class DestinationConfigInline(admin.TabularInline):
    model = DestinationConfig
    ordering = ["media", "label"]
    extra = 1

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_obj = obj
        return super(DestinationConfigInline, self).get_formset(request, obj, **kwargs)

    def get_queryset(self, request):
        qs = super(DestinationConfigInline, self).get_queryset(request)
        return qs.filter(user=self.parent_obj)


class UserAdmin(BaseUserAdmin):
    # inlines = [DestinationConfigInline]

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(User, UserAdmin)
