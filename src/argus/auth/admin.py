from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(User, UserAdmin)
